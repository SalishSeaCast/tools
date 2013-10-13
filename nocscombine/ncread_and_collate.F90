cc ncread_and_collate
cc
cc FORTRAN subroutine that reads in data from the individual local domains and 
cc combines it into a global datafield which is written into a NetCDF archive.
cc
cc INPUT ::
cc           fname -> filename of one of the input NetCDF archives
cc         verbose -> Logical flag to activate report output (for debugging)
cc
      subroutine ncread_and_collate( fname, oname, silent, verbose, showhaloes,
     &                               dovar, doTslice, tstart, tend, noff )

      USE netcdf
      implicit none

      character(LEN=*), intent(in)  :: fname, oname
      logical, intent(in) :: verbose, silent, showhaloes, doTslice
      integer, intent(in) ::  tstart, tend
      integer, intent(in) ::  noff
      integer :: n, varid, varid2, status, ncid, numfiles, itmp,
     &           i, num_instances, Gncid, ig
      integer :: ihs(2), ihe(2)
      integer, dimension(4) :: global_end
      integer, dimension(4) :: global_size
      logical, intent(in) :: dovar(*)
c
c scalars
c
      real             :: tmpv
      integer (KIND=4) :: itmpv
      integer (KIND=2) :: istmpv
      integer (KIND=1) :: ibtmpv
      real (KIND=8)    :: dtmpv
c
c 1d allocatable arrays
c
      real,             dimension(:), allocatable :: times
      integer (KIND=4), dimension(:), allocatable :: itimes
      integer (KIND=2), dimension(:), allocatable :: istimes
      integer (KIND=1), dimension(:), allocatable :: ibtimes
      real (KIND=8),    dimension(:), allocatable :: dtimes
c
c 2d allocatable arrays
c
      real,             dimension(:,:), allocatable :: data_2d
      integer (KIND=4), dimension(:,:), allocatable :: datai_2d
      integer (KIND=2), dimension(:,:), allocatable :: datas_2d
      integer (KIND=1), dimension(:,:), allocatable :: datab_2d
      real (KIND=8),    dimension(:,:), allocatable :: datad_2d
c
c 3d allocatable arrays
c
      real,             dimension(:,:,:), allocatable :: data_3d
      integer (KIND=4), dimension(:,:,:), allocatable :: datai_3d
      integer (KIND=2), dimension(:,:,:), allocatable :: datas_3d
      integer (KIND=1), dimension(:,:,:), allocatable :: datab_3d
      real (KIND=8),    dimension(:,:,:), allocatable :: datad_3d
c
c 4d allocatable arrays
c
      real,             dimension(:,:,:,:), allocatable :: data_4d
      integer (KIND=4), dimension(:,:,:,:), allocatable :: datai_4d
      integer (KIND=2), dimension(:,:,:,:), allocatable :: datas_4d
      integer (KIND=1), dimension(:,:,:,:), allocatable :: datab_4d
      real (KIND=8),    dimension(:,:,:,:), allocatable :: datad_4d
c
      character*256 nname
      integer m, k, nDim, nVar, nAtt, nlen, nunlim,
     &        ntyp, nvatt, ndims, oldMode, npo
      integer, allocatable, dimension(:) :: dims, local_size, global_start,
     &                                      lstart,lsize

      character(LEN=256)            :: fname2
      character(LEN=4)              :: str
#ifdef FIX_DOMATT
      integer :: nread,idum,nlci,nlcj,nldi,nldj,nlei,nlej
#endif
cc
cc Open the input datafile. Read the global domain dimensions and the required
cc number of input files to accessed.
cc
      status = nf90_open( trim(fname), NF90_NOWRITE, ncid )
      status = nf90_enddef( ncid ) 
      status = nf90_Inquire(ncid, nDim, nVar, nAtt, nunlim)
      allocate(dims(nDim))
      allocate(global_start(nDim))
      allocate(local_size(nDim))
      allocate(lstart(nDim))
      allocate(lsize(nDim))

      status = nf90_get_att( ncid, nf90_global, "DOMAIN_size_global", 
     &                       local_size )
      global_size(1) = local_size(1)
      global_size(2) = local_size(2)
      status = nf90_inquire_dimension( ncid, 3, len = global_size(3) )
      status = nf90_inquire_dimension( ncid, 4, len = num_instances )
      allocate(times(num_instances))

      status = nf90_get_att( ncid, nf90_global, "DOMAIN_number_total", 
     &                       numfiles )
cc
cc Read in the number instances contained in the archive
cc
      if(verbose) then
       write(*,*) " "
       write(*,*) "LAST MODEL WRITE ( in seconds)  :: ", times(num_instances)
       write(*,*) "MODEL GLOBAL DIMENSIONS         :: ", global_size
       write(*,*) "TOTAL NUMBER OF PROCESSORS      :: ", numfiles
       write(*,*) " "
      endif
cc
cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
cc Main Data Extraction Process
cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
cc
cc
cc Create the global NetCDF archive.
cc
      CALL make_global_file( fname, oname, times, global_size, 
     &                       num_instances, verbose, dovar )
      deallocate(times)

cc
cc Re-open the global archive in preparation for data transfer
cc
      write(*,'(a)') trim(oname)
      status = nf90_open( trim(oname), NF90_WRITE, Gncid )
      call handle_err(status)
      status = nf90_set_fill(Gncid, NF90_NOFILL, oldMode)
      status = nf90_enddef( Gncid )

      do n = 0, numfiles-1
         npo = MOD(n + noff,numfiles)
         if(.not.silent) write(*,'(a,i2,$)') '[',mod(npo,100)
cc
cc Form appropriate filename and open corresponding NetCDF archive
cc
         itmp = len_trim( fname ) - 7
         write(str,'(i4.4)') npo
         fname2 = fname(1:itmp)//str//".nc"
         status = nf90_open( trim(fname2), NF90_NOWRITE, ncid )
         status = nf90_enddef( ncid )
cc
cc Determine dimensions of local subdomain contained in archive. Then
cc read in where the local data is to be inserted in the global datafield.
cc Allocate enough memory to hold a local 2D and 3D data array.
cc
         status = nf90_get_att( ncid, nf90_global, "DOMAIN_size_local",
     &                          local_size )
         status = nf90_get_att( ncid, nf90_global, "DOMAIN_position_first",
     &                          global_start )
         status = nf90_get_att( ncid, nf90_global, "DOMAIN_position_last",
     &                          global_end )
cc
         if(.not.showhaloes) then
cc
cc Early versions of nocscombine erroneously copied across the halo rows
cc and columns too. Potentially producing lines of unset values if the
cc halo points were not set in the individual restart files (as could
cc happen for some purely diagnostic fields). Use -showhaloes to
cc reproduce this feature if required
cc
          status = nf90_get_att( ncid, nf90_global, "DOMAIN_halo_size_start",
     &                           ihs )
          status = nf90_get_att( ncid, nf90_global, "DOMAIN_halo_size_end",
     &                           ihe )
cc
#ifdef FIX_DOMATT
c
c May be necessary for domain partitions which have thrown away
c land only regions due to faulty logic in mpp_init_ioipsl
c which will have set the wrong halo sizes
c
         if(n.eq.0) 
     &   write(*,*) 'nocscombine test version: fixing domain attributes'
         open(unit=11, file='layout.dat')
         read(11,*)
         read(11,*)
         do nread = 0,n
          read(11,*) idum,nlci,nlcj,nldi,nldj,nlei,nlej
         end do
         close(11)
         ihs(1) = nldi-1
         ihs(2) = nldj-1
         ihe(1) = nlci-nlei
         ihe(2) = nlcj-nlej
#endif
          global_start(1) = global_start(1) + ihs(1) 
          global_start(2) = global_start(2) + ihs(2) 
          global_end(1)   = global_end(1)   - ihe(1) 
          global_end(2)   = global_end(2)   - ihe(2) 
          local_size(1)   = local_size(1)   - (ihs(1) + ihe(1))
          local_size(2)   = local_size(2)   - (ihs(2) + ihe(2))
         endif
cc
         global_end(3) = global_size(3)
         global_end(4) = num_instances
         global_start(3) = 1
         global_start(4) = 1
         local_size(3) = global_size(3)
         local_size(4) = num_instances
cc
         do k = 1,nDim
          status = nf90_Inquire_Dimension(ncid, k, nname, nlen)
          if(k.gt.4) then
           global_start(k) = 1
           local_size(k) = nlen
          endif
         end do
         ig = 0
         do i = 1,nVar
          status = nf90_Inquire_Variable(ncid, i, nname, 
     &                                   ntyp, ndims, dims, nvatt)
c
          call handle_err(status)
         IF(.not.dovar(i)) THEN
c skip unwanted variables
         ELSE
          if(doTslice) local_size(4) = tend - tstart + 1
          lstart = 1
          lsize = local_size
          if(doTslice.and.(dims(ndims).eq.nunlim)) then
           lstart(ndims) = tstart
           lsize(ndims)  = tend - tstart + 1
          endif
          ig = ig + 1
          if(verbose)
     &     write(*,*) i,trim(fname2),' ','Transferring ',trim(nname),ntyp
          if(verbose) write(*,*) ndims,(dims(m),global_start(dims(m)),
     &               local_size(dims(m)),m=1,ndims)
          do k = 1,ndims
           if(dims(k).eq.1) lstart(k) = 1+ihs(1)
           if(dims(k).eq.2) lstart(k) = 1+ihs(2)
          end do
c
          IF(ntyp.eq.NF90_DOUBLE) THEN
c
c DOUBLE PRECISION DATA
c
           if(ndims.eq.0) then
            status = nf90_get_var( ncid,   i, dtmpv )
            status = nf90_put_var( Gncid,  ig, dtmpv )
           elseif(ndims.eq.1) then
            allocate( dtimes(lsize(dims(1))) )
            status = nf90_get_var( ncid,   i, dtimes, start = lstart )
            status = nf90_put_var( Gncid,  ig, dtimes, 
     &         start=(/ 1 /),
     &         count=(/ lsize(dims(1)) /) )
            deallocate(dtimes)
           elseif(ndims.eq.2) then
            allocate( datad_2d(lsize(dims(1)), lsize(dims(2))),
     &                STAT=status)
            if(verbose) write(*,*) '2d Allocate status: ',status
            status = nf90_get_var( ncid,   i, datad_2d, start=lstart )
            status = nf90_put_var( Gncid,  ig, datad_2d,
     &         start=(/ global_start(dims(1)), global_start(dims(2)) /),
     &         count=(/ lsize(dims(1)), lsize(dims(2)) /) )
            deallocate(datad_2d)
           elseif(ndims.eq.3) then
            allocate( datad_3d(lsize(dims(1)), lsize(dims(2)),
     &                         lsize(dims(3))), STAT=status)
            if(verbose) write(*,*) '3d Allocate status: ',status
            status = nf90_get_var( ncid,   i, datad_3d, start=lstart )
            status = nf90_put_var( Gncid,  ig, datad_3d,
     &         start=(/ global_start(dims(1)), global_start(dims(2)), 
     &                  global_start(dims(3)) /),
     &         count=(/ lsize(dims(1)), lsize(dims(2)), 
     &                  lsize(dims(3)) /) )
            deallocate(datad_3d)
           elseif(ndims.eq.4) then
            allocate( datad_4d(lsize(dims(1)), lsize(dims(2)),
     &                        lsize(dims(3)), lsize(dims(4))),
     &                        STAT=status)
            if(verbose) write(*,*) '4d Allocate status: ',status
            status = nf90_get_var( ncid,   i, datad_4d, start= lstart )
            status = nf90_put_var( Gncid,  ig, datad_4d,
     &         start=(/ global_start(dims(1)), global_start(dims(2)),
     &                  global_start(dims(3)), global_start(dims(4)) /),
     &         count=(/ lsize(dims(1)), lsize(dims(2)),
     &                  lsize(dims(3)), lsize(dims(4)) /) )
            deallocate(datad_4d)
           endif
c
          ELSEIF(ntyp.eq.NF90_REAL) THEN
c
c SINGLE PRECISION DATA
c
           if(ndims.eq.0) then
            status = nf90_get_var( ncid,   i, tmpv )
            status = nf90_put_var( Gncid,  ig, tmpv )
           elseif(ndims.eq.1) then
            allocate( times(lsize(dims(1))) )
            status = nf90_get_var( ncid,   i, times, start = lstart )
            status = nf90_put_var( Gncid,  ig, times,
     &         start=(/ 1 /),
     &         count=(/ lsize(dims(1)) /) )
            deallocate(times)
           elseif(ndims.eq.2) then
            allocate( data_2d(lsize(dims(1)), lsize(dims(2))),
     &                STAT=status)
            if(verbose) write(*,*) '2d Allocate status: ',status
            status = nf90_get_var( ncid,   i, data_2d, start= lstart )
            if(verbose) write(*,*) 'Got 2d data '
            status = nf90_put_var( Gncid,  ig, data_2d,
     &         start=(/ global_start(dims(1)), global_start(dims(2)) /),
     &         count=(/ lsize(dims(1)), lsize(dims(2)) /) )
            deallocate(data_2d)
           elseif(ndims.eq.3) then
            allocate( data_3d(lsize(dims(1)), lsize(dims(2)),
     &                         lsize(dims(3))), STAT=status)
            if(verbose) write(*,*) '3d Allocate status: ',status
            status = nf90_get_var( ncid,   i, data_3d, start= lstart )
            status = nf90_put_var( Gncid,  ig, data_3d,
     &         start=(/ global_start(dims(1)), global_start(dims(2)),
     &                  global_start(dims(3)) /),
     &         count=(/ lsize(dims(1)), lsize(dims(2)),
     &                  lsize(dims(3)) /) )
            deallocate(data_3d)
           elseif(ndims.eq.4) then
            allocate( data_4d(lsize(dims(1)), lsize(dims(2)),
     &                        lsize(dims(3)), lsize(dims(4))),
     &                        STAT=status)
            if(verbose) write(*,*) '4d Allocate status: ',status
            status = nf90_get_var( ncid,   i, data_4d, start= lstart )
            status = nf90_put_var( Gncid,  ig, data_4d,
     &         start=(/ global_start(dims(1)), global_start(dims(2)),
     &                  global_start(dims(3)), global_start(dims(4)) /),
     &         count=(/ lsize(dims(1)), lsize(dims(2)),
     &                  lsize(dims(3)), lsize(dims(4)) /) )
            deallocate(data_4d)
           endif
c
          ELSEIF(ntyp.eq.NF90_INT) THEN
c
c 32-bit INTEGER DATA
c
           if(ndims.eq.0) then
            status = nf90_get_var( ncid,   i, itmpv )
            status = nf90_put_var( Gncid,  ig, itmpv )
           elseif(ndims.eq.1) then
            allocate( itimes(lsize(dims(1))) )
            if(verbose) write(*,*) '1d Allocate status: ',status, 
     &                              lsize(dims(1))
            status = nf90_get_var( ncid,   i, itimes, start = lstart )
            status = nf90_put_var( Gncid,  ig, itimes,
     &         start=(/ 1 /),
     &         count=(/ lsize(dims(1)) /) )
            if(verbose) write(*,*) '1d put status: ',status 
            deallocate(itimes)
           elseif(ndims.eq.2) then
            allocate( datai_2d(lsize(dims(1)), lsize(dims(2))),
     &               STAT=status)
            if(verbose) write(*,*) '2d Allocate status: ',status
            status = nf90_get_var( ncid,   i, datai_2d, start= lstart )
            status = nf90_put_var( Gncid,  ig, datai_2d,
     &         start=(/ global_start(dims(1)), global_start(dims(2)) /),
     &         count=(/ lsize(dims(1)), lsize(dims(2)) /) )
            deallocate(datai_2d)
           elseif(ndims.eq.3) then
            allocate( datai_3d(lsize(dims(1)), lsize(dims(2)),
     &                         lsize(dims(3))), STAT=status)
            if(verbose) write(*,*) '3d Allocate status: ',status
            status = nf90_get_var( ncid,   i, datai_3d, start= lstart )
            status = nf90_put_var( Gncid,  ig, datai_3d,
     &         start=(/ global_start(dims(1)), global_start(dims(2)),
     &                  global_start(dims(3)) /),
     &         count=(/ lsize(dims(1)), lsize(dims(2)),
     &                  lsize(dims(3)) /) )
            deallocate(datai_3d)
           elseif(ndims.eq.4) then
            allocate( datai_4d(lsize(dims(1)), lsize(dims(2)),
     &                        lsize(dims(3)), lsize(dims(4))),
     &                        STAT=status)
            if(verbose) write(*,*) '4d Allocate status: ',status
            status = nf90_get_var( ncid,   i, datai_4d, start= lstart )
            status = nf90_put_var( Gncid,  ig, datai_4d,
     &         start=(/ global_start(dims(1)), global_start(dims(2)),
     &                  global_start(dims(3)), global_start(dims(4)) /),
     &         count=(/ lsize(dims(1)), lsize(dims(2)),
     &                  lsize(dims(3)), lsize(dims(4)) /) )
            deallocate(datai_4d)
           endif
c
          ELSEIF(ntyp.eq.NF90_SHORT) THEN
c
c 16-bit INTEGER DATA
c
           if(ndims.eq.0) then
            status = nf90_get_var( ncid,   i, istmpv )
            status = nf90_put_var( Gncid,  ig, istmpv )
           elseif(ndims.eq.1) then
            allocate( istimes(lsize(dims(1))) )
            if(verbose) write(*,*) '1d Allocate status: ',status, 
     &                              lsize(dims(1))
            status = nf90_get_var( ncid,   i, istimes, start = lstart )
            status = nf90_put_var( Gncid,  ig, istimes,
     &         start=(/ 1 /),
     &         count=(/ lsize(dims(1)) /) )
            if(verbose) write(*,*) '1d put status: ',status 
            deallocate(istimes)
           elseif(ndims.eq.2) then
            allocate( datas_2d(lsize(dims(1)), lsize(dims(2))),
     &               STAT=status)
            if(verbose) write(*,*) '2d Allocate status: ',status
            status = nf90_get_var( ncid,   i, datas_2d, start= lstart )
            status = nf90_put_var( Gncid,  ig, datas_2d,
     &         start=(/ global_start(dims(1)), global_start(dims(2)) /),
     &         count=(/ lsize(dims(1)), lsize(dims(2)) /) )
            deallocate(datas_2d)
           elseif(ndims.eq.3) then
            allocate( datas_3d(lsize(dims(1)), lsize(dims(2)),
     &                         lsize(dims(3))), STAT=status)
            if(verbose) write(*,*) '3d Allocate status: ',status
            status = nf90_get_var( ncid,   i, datas_3d, start= lstart )
            status = nf90_put_var( Gncid,  ig, datas_3d,
     &         start=(/ global_start(dims(1)), global_start(dims(2)),
     &                  global_start(dims(3)) /),
     &         count=(/ lsize(dims(1)), lsize(dims(2)),
     &                  lsize(dims(3)) /) )
            deallocate(datas_3d)
           elseif(ndims.eq.4) then
            allocate( datas_4d(lsize(dims(1)), lsize(dims(2)),
     &                        lsize(dims(3)), lsize(dims(4))),
     &                        STAT=status)
            if(verbose) write(*,*) '4d Allocate status: ',status
            status = nf90_get_var( ncid,   i, datas_4d, start= lstart )
            status = nf90_put_var( Gncid,  ig, datas_4d,
     &         start=(/ global_start(dims(1)), global_start(dims(2)),
     &                  global_start(dims(3)), global_start(dims(4)) /),
     &         count=(/ lsize(dims(1)), lsize(dims(2)),
     &                  lsize(dims(3)), lsize(dims(4)) /) )
            deallocate(datas_4d)
           endif
c
          ELSEIF(ntyp.eq.NF90_BYTE) THEN
c
c 8-bit INTEGER DATA
c
           if(ndims.eq.0) then
            status = nf90_get_var( ncid,   i, ibtmpv )
            status = nf90_put_var( Gncid,  ig, ibtmpv )
           elseif(ndims.eq.1) then
            allocate( itimes(lsize(dims(1))) )
            if(verbose) write(*,*) '1d Allocate status: ',status, 
     &                              lsize(dims(1))
            status = nf90_get_var( ncid,   i, ibtimes, start = lstart )
            status = nf90_put_var( Gncid,  ig, ibtimes,
     &         start=(/ 1 /),
     &         count=(/ lsize(dims(1)) /) )
            if(verbose) write(*,*) '1d put status: ',status 
            deallocate(ibtimes)
           elseif(ndims.eq.2) then
            allocate( datab_2d(lsize(dims(1)), lsize(dims(2))),
     &               STAT=status)
            if(verbose) write(*,*) '2d Allocate status: ',status
            status = nf90_get_var( ncid,   i, datab_2d, start= lstart )
            status = nf90_put_var( Gncid,  ig, datab_2d,
     &         start=(/ global_start(dims(1)), global_start(dims(2)) /),
     &         count=(/ lsize(dims(1)), lsize(dims(2)) /) )
            deallocate(datab_2d)
           elseif(ndims.eq.3) then
            allocate( datab_3d(lsize(dims(1)), lsize(dims(2)),
     &                         lsize(dims(3))), STAT=status)
            if(verbose) write(*,*) '3d Allocate status: ',status
            status = nf90_get_var( ncid,   i, datab_3d, start= lstart )
            status = nf90_put_var( Gncid,  ig, datab_3d,
     &         start=(/ global_start(dims(1)), global_start(dims(2)),
     &                  global_start(dims(3)) /),
     &         count=(/ lsize(dims(1)), lsize(dims(2)),
     &                  lsize(dims(3)) /) )
            deallocate(datab_3d)
           elseif(ndims.eq.4) then
            allocate( datab_4d(lsize(dims(1)), lsize(dims(2)),
     &                        lsize(dims(3)), lsize(dims(4))),
     &                        STAT=status)
            if(verbose) write(*,*) '4d Allocate status: ',status
            status = nf90_get_var( ncid,   i, datab_4d, start= lstart )
            status = nf90_put_var( Gncid,  ig, datab_4d,
     &         start=(/ global_start(dims(1)), global_start(dims(2)),
     &                  global_start(dims(3)), global_start(dims(4)) /),
     &         count=(/ lsize(dims(1)), lsize(dims(2)),
     &                  lsize(dims(3)), lsize(dims(4)) /) )
            deallocate(datab_4d)
           endif
          ENDIF
          call handle_err(status)
         ENDIF
         enddo
cc
cc Close the input NetCDF archive and write some info to the screen
cc
         status = nf90_close( ncid )

         if(verbose) then
          write(*,*) "INPUT FILENAME               :: ", trim(fname2)
          write(*,*) 'MODEL FILE LOCAL DIMENSIONS  :: ', local_size
          write(*,*) 'MODEL FILE GLOBAL START      :: ', global_start 
          write(*,*) 'MODEL FILE GLOBAL END        :: ', global_end
          write(*,*) ' '
         endif
         if(.not.silent) write(*,'(a,$)') '] '
      enddo
      if(.not.silent) write(*,*) 'Done'
      deallocate(dims)
      deallocate(local_size)
      deallocate(global_start)
      deallocate(lsize)
      deallocate(lstart)
      status = nf90_close( Gncid )

      end subroutine 
