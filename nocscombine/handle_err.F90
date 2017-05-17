      subroutine handle_err(status)
      USE NETCDF
        integer, intent ( in) :: status
   
        if(status /= nf90_noerr) then
          write(*,*) trim(nf90_strerror(status))
          stop "Stopped"
        end if
      end subroutine handle_err
