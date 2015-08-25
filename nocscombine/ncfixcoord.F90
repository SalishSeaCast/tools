cc ncfixcoord
cc
cc FORTRAN subroutine that reads in nav_lon and nav_lat from a supplied
cc coordinate file and uses these fields to replace existing nav_lon
cc and nav_lat fields in a collated dataset.
cc
cc This routine is normally only required when the collated dataset
cc was constructed from a parallel run which had ignored land-only
cc regions (i.e. jpnij < jpni*jpnj )
cc
cc Any attempt will be abandoned if the input fields do not match the 
cc fields they are to replace in either rank, size or datatype
cc
cc INPUT ::
cc           oname  -> filename of a collated NetCDF file
cc        coordname -> filename of a NEMO coordinates file
cc
      subroutine ncfixcoord( oname, coordname, verbose)

      USE netcdf
      implicit none

      character(LEN=*), intent(in)  :: oname, coordname
      logical, intent(in)  :: verbose
      integer :: n, status, ncid, Gncid
      integer, dimension(2) :: Gvarid, varid
c
c 2d allocatable arrays
c
      real,             dimension(:,:), allocatable :: data_2d
      integer (KIND=4), dimension(:,:), allocatable :: datai_2d
      integer (KIND=2), dimension(:,:), allocatable :: datas_2d
      integer (KIND=1), dimension(:,:), allocatable :: datab_2d
      real (KIND=8),    dimension(:,:), allocatable :: datad_2d
c
      character*256 nname
      integer m, k, nDim, nVar, nAtt, nlen, nunlim, i,
     &        ntyp, nvatt, ndims, oldMode, ntyp2, ndims2
      integer, allocatable, dimension(:) :: dims, gsize, lsize

cc
cc Open the coordinate datafile. Read the global domain dimensions 
cc
      status = nf90_open( trim(coordname), NF90_NOWRITE, Gncid )
      if(status /= nf90_NoErr) call handle_err(status)
cc
      status = nf90_inq_varid(Gncid, "nav_lon", Gvarid(1))
      if(status /= nf90_NoErr) call handle_err(status)
      status = nf90_inq_varid(Gncid, "nav_lat", Gvarid(2))
      if(status /= nf90_NoErr) call handle_err(status)
cc
      status = nf90_Inquire(Gncid, nDim, nVar, nAtt, nunlim)
      allocate(dims(nDim))
      allocate(gsize(nDim))
      allocate(lsize(nDim))
cc
      status = nf90_Inquire_Variable(Gncid, Gvarid(1), nname, 
     &                               ntyp, ndims, dims, nvatt)
cc
      if(verbose) write(*,*)'Fixing coordinates, name: ',trim(nname)
      do i = 1,ndims
       status = nf90_inquire_dimension( Gncid, i, len = gsize(i) )
       if(verbose) write(*,*)'Fixing coordinates, dimension ',i,gsize(i)
      end do
cc
      status = nf90_open( trim(oname), NF90_WRITE, ncid )
      if(status /= nf90_NoErr) call handle_err(status)
      if(verbose) write(*,*)'Fixing coordinates in ',trim(oname)
      status = nf90_inq_varid(ncid, "nav_lon", varid(1))
      if(status /= nf90_NoErr) call handle_err(status)
      status = nf90_inq_varid(ncid, "nav_lat", varid(2))
      if(status /= nf90_NoErr) call handle_err(status)
      status = nf90_Inquire_Variable(ncid, varid(1), nname, 
     &                               ntyp2, ndims2, dims, nvatt)
      if(status /= nf90_NoErr) call handle_err(status)
      if(verbose) write(*,*)'Fixing coordinates, ndims ',ndims
      if(ndims /= 2 .or. ndims2 /= 2 ) then
        write(*,*) 'nav_lon is not 2-dimensional'
        write(*,*) 'attempt to fix nav_lon and nav_lat abandoned'
        status = nf90_close( Gncid )
        status = nf90_close( ncid )
        return
       endif
      if(verbose) write(*,*)'Fixing coordinates, type ',ntyp2
      if(ntyp2 /= ntyp ) then
        write(*,*) 'Coordinate file and collated file datatype mismatch'
        write(*,*) 'attempt to fix nav_lon and nav_lat abandoned'
        status = nf90_close( Gncid )
        status = nf90_close( ncid )
        return
       endif
cc
      do i = 1,ndims
       status = nf90_inquire_dimension( ncid, i, len = lsize(i) )
       if(status /= nf90_NoErr) call handle_err(status)
       if(verbose) write(*,*)'Fixing coordinates, ldims ',i,lsize(i)
       if(lsize(i) /= gsize(i)) then
        write(*,*) 'Coordinate file and collated file size mismatch'
        write(*,*) 'attempt to fix nav_lon and nav_lat abandoned'
        status = nf90_close( Gncid )
        status = nf90_close( ncid )
        return
       endif
      end do
cc
      do n=1,2
       if(verbose) write(*,*)'Fixing coordinates, type ',n,ntyp
          IF(ntyp.eq.NF90_DOUBLE) THEN
c
c DOUBLE PRECISION DATA
c
            allocate( datad_2d(lsize(1), lsize(2)),
     &                STAT=status)
            status = nf90_get_var( Gncid,   Gvarid(n), datad_2d )
            status = nf90_put_var( ncid,  varid(n), datad_2d )
            deallocate(datad_2d)
c
          ELSEIF(ntyp.eq.NF90_REAL) THEN
c
c SINGLE PRECISION DATA
c
            allocate( data_2d(lsize(1), lsize(2)),
     &                STAT=status)
            status = nf90_get_var( Gncid, Gvarid(n), data_2d )
            status = nf90_put_var( ncid,  varid(n), data_2d )
            deallocate(data_2d)
c
          ELSEIF(ntyp.eq.NF90_INT) THEN
c
c 32-bit INTEGER DATA
c
            allocate( datai_2d(lsize(1), lsize(2)),
     &               STAT=status)
            status = nf90_get_var( Gncid, Gvarid(n), datai_2d )
            status = nf90_put_var( ncid,  varid(n), datai_2d )
            deallocate(datai_2d)
c
          ELSEIF(ntyp.eq.NF90_SHORT) THEN
c
c 16-bit INTEGER DATA
c
            allocate( datas_2d(lsize(1), lsize(2)),
     &               STAT=status)
            status = nf90_get_var( Gncid,   Gvarid(n), datas_2d )
            status = nf90_put_var( ncid,  varid(n), datas_2d )
            deallocate(datas_2d)
c
          ELSEIF(ntyp.eq.NF90_BYTE) THEN
c
c 8-bit INTEGER DATA
c
            allocate( datab_2d(lsize(1), lsize(2)),
     &               STAT=status)
            status = nf90_get_var( Gncid,   Gvarid(n), datab_2d )
            status = nf90_put_var( ncid,  varid(n), datab_2d )
            deallocate(datab_2d)
          ENDIF
          call handle_err(status)
         enddo
cc
cc Close the NetCDF files
cc
         status = nf90_close( ncid )
         status = nf90_close( Gncid )

      deallocate(dims)
      deallocate(gsize)
      deallocate(lsize)

      end subroutine 
