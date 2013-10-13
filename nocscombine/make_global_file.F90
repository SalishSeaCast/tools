cc make_global_file
cc
cc FORTRAN subroutine that defines the global NetCDF archive containing
cc diagnostics on the T-grid.  The archive is given the default name of
cc "global_Tgrid.nc" 
cc 
cc INPUT ::
cc       my_time -> array containing write times in seconds
cc       my_size -> array containing sizes of global archive dimensions
cc     num_times -> number of time records in archive
cc
      subroutine make_global_file( infile, ofile, my_time, my_size3, 
     &                             num_times, verbose, dovar )

      USE netcdf
      implicit none
 
      integer, intent(IN)               :: num_times
      logical, intent(IN)               :: verbose
      integer, dimension(3), intent(IN) :: my_size3
      integer, dimension(4)             :: my_size
      real, dimension(99)               :: my_time
      logical                           :: dovar(*)

      integer                :: status, ncid, varID, ncid2
      integer, allocatable, dimension(:)  :: dimID,dims,sdims

      real,dimension(:), allocatable :: depth_array
      character*(*) infile, ofile
      character*256 nname
      integer i, m, k, nDim, nVar, nAtt, nlen, nunlim, 
     &        n, ntyp, nvatt, ndims, oldfill
cc
cc Create global archive and set dimensions
cc
      my_size(1:3) = my_size3
      my_size(4) = num_times
#ifdef LARGE_FILE
      status = nf90_create( trim(ofile), 
     &         cmode=or(nf90_clobber,nf90_64bit_offset), 
     &         ncid=ncid )
#else
      status = nf90_create( trim(ofile), NF90_CLOBBER, ncid )
#endif
      call handle_err(status)
      if(verbose) write(*,*) 'File opened: ', status
      status = nf90_set_fill(ncid, NF90_NOFILL, oldfill)
      if(verbose) write(*,*) 'Old fillmode/new: ',oldfill,NF90_NOFILL
c
c
      status = nf90_open(infile,NF90_NOWRITE,ncid2)
      status = nf90_Inquire(ncid2, nDim, nVar, nAtt, nunlim)
      allocate(dimID(nDim))
      allocate(dims(nDim))
      allocate(sdims(nDim))
      if(verbose) write(*,*) 'Dimensions: '
      do n = 1,nDim
       status = nf90_Inquire_Dimension(ncid2, n, nname, nlen)
       if(verbose) write(*,*) n,nlen,' ',trim(nname)
       sdims(n) = nlen
       if(n.eq.nunlim) then
        status = nf90_def_dim( ncid,trim(nname), nf90_unlimited, dimID(n) )
        if(verbose) write(*,*) 'Unlimited dim ',n,my_size(n),' currently'
       elseif(n.le.4) then
        status = nf90_def_dim( ncid,trim(nname), my_size(n), dimID(n) )
       else
        status = nf90_def_dim( ncid,trim(nname), nlen, dimID(n) )
       endif
      end do
      if(verbose) write(*,*) 'Variables: '
      do n=1,nVar
       if(n.ne.1) then
        status =  nf90_redef(ncid)
        call handle_err(status)
       endif
       status = nf90_Inquire_Variable(ncid2, n, nname, ntyp, ndims, dims, nvatt)
c
      IF(.not.dovar(n)) THEN
c skip unwanted variables
      ELSE
       if(verbose) 
     &         write(*,*) n,ntyp,ndims,(dims(i),i=1,ndims),nvatt,' ',trim(nname)
       if(ndims.eq.0) then
        status = nf90_def_var( ncid, trim(nname), ntyp,  varID )
       elseif(ndims.eq.1) then
        status = nf90_def_var( ncid, trim(nname), ntyp,
     &                      (/ dimID(dims(1)) /), varID )
       elseif(ndims.eq.2) then
        status = nf90_def_var( ncid, trim(nname), ntyp,
     &                      (/ dimID(dims(1)), dimID(dims(2)) /), varID )
       if(verbose) write(*,*) 'dimids ',dimID(dims(1)),dimID(dims(2))
       elseif(ndims.eq.3) then
        status = nf90_def_var( ncid, trim(nname), ntyp,
     &                      (/ dimID(dims(1)), dimID(dims(2)), 
     &                         dimID(dims(3)) /), varID )
       elseif(ndims.eq.4) then
        status = nf90_def_var( ncid, trim(nname), ntyp,
     &                      (/ dimID(dims(1)), dimID(dims(2)), 
     &                         dimID(dims(3)), dimID(dims(4)) /), varID )
       else
        write(*,*) 'Unknown ndims: ',ndims
       endif
       call handle_err(status)
       do m = 1,nvatt
        status = nf90_Inq_Attname(ncid2,n,m,nname)
        if(verbose) write(*,*) '  ',n,m,' ',trim(nname)
        status = nf90_copy_att(ncid2,n,trim(nname),ncid,varID)
        call handle_err(status)
       end do
      ENDIF
       if(verbose) write(*,*) n,' Calling enddef in make_global_file4'
       status = nf90_enddef(ncid)
       call handle_err(status)
      end do
      deallocate(dimID)
      deallocate(dims)
      deallocate(sdims)
c      
c Global Attributes:
c      
      status = nf90_redef(ncid)
      call handle_err(status)
      do n = 1,nAtt
       status = nf90_Inq_Attname(ncid2,NF90_GLOBAL,n,nname)
       if(verbose) write(*,*) 'Global Attribute: ',n,' ',trim(nname)
       if(.not. (index(nname,'DOMAIN').gt.0    .or.
     &           index(nname,'associate').gt.0 .or.
     &           index(nname,'file_name').gt.0  )) 
     &  status = nf90_copy_att(ncid2,
     &                     NF90_GLOBAL,trim(nname),ncid,NF90_GLOBAL)
        call handle_err(status)
      end do
344   if(verbose) write(*,*) '0.Calling enddef in make_global_file'
      status = nf90_enddef(ncid)
      call handle_err(status)
      if(verbose) write(*,*) 'A.Finished make_global_file'
      status = nf90_close(ncid)
      call handle_err(status)
      if(verbose) write(*,*) 'B.Finished make_global_file'
      end 
