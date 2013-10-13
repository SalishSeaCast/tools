cc nocscombine
cc
cc FORTRAN program that assembles a global NetCDF archive from a series of 
cc NEMO output files.
cc
cc USAGE :: nocscombine -f inputfile [-o outfile] [-v] [-s]
cc                      [-d list of variables] [-ts tstart] [-te tend]
cc
cc      -f  inputfile  
cc          Mandatory argument. inputfile is the filename of 
cc          one of the NEMO restart or diagnostic files.  
cc          This should be the whole filename of one of the individual
cc          processor files (i.e. include the 
cc          node number, eg. ORCA1_00010101_restart_0012.nc).
cc          This program works on NetCDF NEMO output files. The program will
cc          create a NetCDF archive covering the entire global domain.  
cc
cc     [-o outputfile ] 
cc          Optional argument. outputfilename is the required name
cc          of the outputfile. By default this name will be constructed from
cc          the inputfilename by stripping off the processor number. I.e.:
cc          inputfile : ORCA1_00010101_restart_0012.nc
cc          outputfile: ORCA1_00010101_restart.nc
cc          The -o option permits the user to override this behaviour.
cc
cc     [-c coordinatefile ] 
cc          Optional argument. coordinatefile is the name
cc          of the global coordinate file relevant to the NEMO model which
cc          produced the individual processor files. This file is required to
cc          ensure complete nav_lon and nav_lat fields in cases where wholly
cc          land areas have been omitted from a parallel run (i.e. 
cc          jpnij .ne. jpni*jpnj). The corrections are applied after
cc          the collation phase. If this argument is supplied and the output
cc          file exists then the collation phase is not performed but the
cc          coordinate corrections are still applied. In the latter scenario
cc          the (otherwise) mandatory inputfile argument is not required.
cc
cc     [-n processor_offset ]
cc          Optional argument. Start collating from this processor number and
cc          process domains in order, cycling back through 0 if necessary. This
cc          is useful to prevent multiple simulataneous accesses when running
cc          nocscombine in a task-farming environment
cc
cc     [-v] 
cc          Optional argument. Switches on verbose reporting for debugging
cc
cc     [-s] 
cc          Optional argument. Normal behaviour is to show a limited amount
cc          of progress information. This option runs the utility without any
cc          output to stdout.
cc
cc     [-showhaloes]
cc          Optional argument. Early versions of nocscombine erroneously 
cc          copied across the halo rows and columns too. Potentially producing 
cc          lines of unset values if the halo points were not set in the 
cc          individual restart files (as could happen for some purely 
cc          diagnostic fields). Use -showhaloes to reproduce this feature 
cc          if required.
cc
cc     [-d] comma-separated list of variables
cc          Collate only the named datasets
cc
cc     [-ts] time-slice (integer) to begin extraction at
cc
cc     [-te] time-slice (integer) to end extraction at
cc
cc
cc Disclaimer
cc ----------
cc Unless otherwise indicated, all other software has been authored
cc by an employee or employees of the National Oceanography Centre,
cc Southampton, UK (NOCS).  NOCS operates as a collaboration
cc between the Natural Environment Research Council (NERC) and
cc the University of Southampton.  The public may copy and use
cc this software without charge, provided that this Notice and
cc any statement of authorship are reproduced on all copies.
cc Neither NERC nor the University makes any warranty, express
cc or implied, or assumes any liability or responsibility for the
cc use of this software.
cc
      program combine

      implicit none

      integer,dimension(10) :: pos
      integer :: time_start = 1, time_end = 0
      integer :: npoff = 0
      real :: runtime
      real, external :: rtime
      logical :: verbose     = .false.
      logical :: silent      = .false.
      logical :: setoname    = .false.
      logical :: showhaloes  = .false.
      logical :: setvname    = .false.
      logical :: tslice      = .false.
      logical :: docollation = .true.
      logical :: fixcoord    = .false.
      logical :: around      = .false.
      character(LEN=256)  :: fname, oname, coordname
      character(LEN=1024) :: inarg, cmdline
      character(LEN=1024) :: varonly
      logical, allocatable :: dovar(:)

      call ParseCmdLine
cc
cc Perform some simple filename checks to determine filetype
cc
      pos(1) = index( fname, ".nc" )
cc
cc Using preceived filetype, call the appropriate routine or stop
cc
      write(*,*) " "
      if ( pos(1).gt.0 .or. fixcoord ) then
            if(.not.setoname) then
             oname = fname(1:pos(1)-6)//'.nc'
             if(.not.silent) 
     &           write(*,'(a)') 'Creating outputfile: '//trim(oname)
            endif
            inquire(file=trim(oname),exist = around)
            if(around.and.fixcoord) docollation = .false.

            if(.not.silent) runtime = rtime(0.0)
            CALL flagvars
            if(docollation) CALL ncread_and_collate( fname, oname, silent, 
     &                               verbose, showhaloes, dovar, tslice,
     &                               time_start, time_end, npoff )
cc
            if(fixcoord) CALL ncfixcoord(oname, coordname, verbose)
cc
            if(.not.silent) then
               runtime = rtime(0.0)
               write(*,'(a,f12.3,a)') 'Completed in ',runtime,' seconds'
            endif

      endif

      CONTAINS

      subroutine ParseCmdLine
      implicit none
c
c Local Vars:
c
      integer n, nargs, na, nb
c
c Function for number of arguments:
c
      integer, external :: iargc
c
      na = 0
      nb = 0
      nargs = iargc()
c
      call getarg(0,cmdline)
      do n = 1, nargs
       call getarg(n,inarg)
       if(    index(trim(inarg),' ').ne.0
     &    .or.index(trim(inarg),',').ne.0) then
        cmdline = trim(cmdline)//' "'//trim(inarg)//'"'
       else
        cmdline = trim(cmdline)//' '//trim(inarg)
       endif
      end do
c
      do n = 1, nargs,1
           na = na + 1
           if(na .gt. nargs) goto 10
           call getarg(na, inarg)
           if(inarg(2:2) .eq. 'f')then
                nb = nb + 1
                na = na + 1
                call getarg(na, inarg)
                read(inarg, '(a)') fname
           else if(inarg(2:2) .eq. 'o')then
                na = na + 1
                call getarg(na, inarg)
                read(inarg, '(a)') oname
                setoname = .true.
           else if(inarg(2:2) .eq. 'c')then
                nb = nb + 1
                na = na + 1
                call getarg(na, inarg)
                read(inarg, '(a)') coordname
                fixcoord = .true.
           else if(inarg(2:11) .eq. 'showhaloes') then
                showhaloes = .true.
           else if(inarg(2:2) .eq. 'v') then
                verbose = .true.
           else if(inarg(2:2) .eq. 's') then
                silent = .true.
                verbose = .false.
           else if(inarg(2:2) .eq. 'd')then
                na = na + 1
                call getarg(na, inarg)
                read(inarg, '(a)') varonly
                setvname = .true.
           else if(inarg(2:3) .eq. 'ts')then
                na = na + 1
                call getarg(na, inarg)
                read(inarg, *) time_start
                tslice = .true.
           else if(inarg(2:3) .eq. 'te')then
                na = na + 1
                call getarg(na, inarg)
                read(inarg, *) time_end
           else if(inarg(2:2) .eq. 'n')then
                na = na + 1
                call getarg(na, inarg)
                read(inarg, *) npoff
           endif
      enddo
10    continue
c
c Default to one time slice if the end time is not given
c
      if(tslice.and.time_end.eq.0) time_end = time_start
c
      if(nb .lt. 1) then
               write(6,*) 'Usage: nocscombine -f infile ',
     &              '[-o outfile] [-c coordfile] ',
     &              '[-v] [-s] [-showhaloes] ',
     &              '[-d comma-separated_list_of_vars] ',
     &              '[-ts t_start] [-te t_end] ',
     &              '[-n processor_offset]'
        stop
      endif
      end subroutine ParseCmdLine

      subroutine flagvars
c
      USE netcdf
      integer :: n, varid, status, ncid, numfiles, 
     &           i, num_instances 
      character (LEN=256) :: nname
      character (LEN=256), allocatable :: dnames(:)
      integer m, k, nDim, nVar, nAtt, nlen, nunlim,
     &        ntyp, nvatt, ndims
      integer, allocatable, dimension(:)  :: dims
c
      CHARACTER(LEN=1024), ALLOCATABLE :: inc(:)
      INTEGER :: incl,ilen,ilast,nv
c
c Firstly derive a list of variables to be included from any
c supplied, comma-separated, list
c
      if( setvname ) then
       allocate(inc(256))
       ilen = len_trim(varonly)
       n = 0
       ilast = 1
       do
        i = index(varonly(ilast:ilen),',')
        n=n+1
        if(i.eq.0) then
         inc(n)=trim(adjustl(varonly(ilast:ilen)))
         exit
        endif
        if(i.eq.1) then
c
c Adjacent commas found; skip this one
c
         n= n-1
        else
         inc(n) = trim(adjustl(varonly(ilast:ilast+i-2)))
c       write(6,*) n,i,ilast,varonly(ilast:ilast+i-2)
        endif
        ilast = i+ilast
c
c Avoid empty strings
c
        if(len_trim(inc(n)).eq.0) n= n-1
        if(n.eq.255) then
         write(*,*) 'Error: internal capacity of inc (flagvars) exceeded'
         stop
        endif
       end do
c
c Check the last one in case of trailing commas
c
       if(len_trim(inc(n)).eq.0) n= n-1
c
       if(verbose) then
        do i = 1,n
         write(6,'(i4,a1,a,a1)') i,'"',trim(inc(i)),'"'
        end do
       endif
       nv = n
      endif
c
      status = nf90_open( trim(fname), NF90_NOWRITE, ncid )
      status = nf90_enddef( ncid )
      status = nf90_Inquire(ncid, nDim, nVar, nAtt, nunlim)
c
      allocate(dnames(nDim))
      allocate(dims(nDim))
c
      do k = 1,nDim
       status = nf90_Inquire_Dimension(ncid, k, nname, nlen)
       dnames(k) = trim(nname)
      end do
c
      allocate(dovar(nVar))
      dovar = .false.
      if (.not.setvname) then
c
c Include every variable
c
       dovar = .true.
c
      else
c
c Compare names against inclusion list
c
       do i = 1,nVar
        status = nf90_Inquire_Variable(ncid, i, nname,
     &                                 ntyp, ndims, dims, nvatt)
        do k =1,nv
         if(trim(nname).eq.trim(inc(k))) then
          dovar(i) = .true.
          exit
         endif
        end do
c
        if(.not.dovar(i)) then
c
c Flag coordinate variables for inclusion even when only a named datasets
c have been requested
c
         do k =1,nDim
          if(trim(dnames(k)).eq.trim(nname)) then
           dovar(i) = .true.
           exit
          endif
         end do
c
c Additionally ensure that nav_lon and nav_lat are copied across
c
         if(trim(nname).eq.'nav_lon'.or.
     &      trim(nname).eq.'nav_lat') dovar(i) = .true.
        endif
       end do
       deallocate(inc)
      endif
c
      deallocate(dnames)
      deallocate(dims)
c
      end subroutine flagvars

      end program combine
