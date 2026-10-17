#include "cfx5ext.h"
C=======================================================================
C
C  MINIMAL REPRODUCER - wall film + rotating domain + breakage into two
C  fragments.  CFX 2023 R2 (v232).
C
C  This routine contains no breakage model of any kind.  Every impact on
C  the film wall produces exactly two fragments, and both are launched
C  with hardcoded coefficients of restitution
C
C        CPER = CPAR = 0.500
C
C  so the correct answer is known exactly and needs no model: measured in
C  the frame of the wall, every fragment must leave with
C
C        NCOR = 0.500,  TCOR = 0.500,  |v_out| / |v_in| = 0.500
C
C  The routine returns the child velocity in the same frame CFX supplied
C  the impact velocity in, i.e. relative to the wall.  Which frame CFX
C  expects the returned value to be in is precisely what we are asking:
C  the documentation we have found does not say, and on a stationary
C  wall the question does not arise because the two frames coincide.
C
C  ---- interface -------------------------------------------------------
C
C  Argument Variables List (NARG = 8):
C        Velocity                  ARG(1,1..3)
C        Mean Particle Diameter    ARG(1,4)
C        Particle Number Rate      ARG(1,5)
C        Particle Position         ARG(1,6..8)
C
C  Return Variables List, with max children = 2 (NRET = 7*NCH = 14):
C        Child Droplet Breakup Indicator   RET(1,1..2)
C        Child Droplet Diameter            RET(1,3..4)
C        Child Droplet Number Rate         RET(1,5..6)
C        Child Droplet Velocity            RET(1,7..12)  child-major
C        Child Droplet Mode                RET(1,13..14)
C
C  The velocity block is CHILD-MAJOR: child i owns
C  RET(1, 3*NCH + 3*(i-1) + 1 .. +3).  Child mode must be 1
C  (__regular_particle__); a child written with mode 0 never launches.
C
C  The film wall is the flat box floor at y = -0.005, so its outward
C  normal is exactly (0,1,0) in the rotating frame and is hardcoded.  No
C  Additional Variables are needed to supply it.
C
C=======================================================================
dllexport(pt_frag_wallframe)
      SUBROUTINE PT_FRAG_WALLFRAME (NLOC,NRET,NARG,RET,ARG,CRESLT,
     &                              CZ,DZ,IZ,LZ,RZ)
C
      IMPLICIT NONE
C
C     No CFX includes are needed beyond cfx5ext.h at the top of the file: this
C     routine uses nothing from cfd_constants.h or stack_point.h, every constant
C     it needs being hardcoded below. (Including them here fails anyway - they
C     expand to executable statements, so any declaration after them draws
C     "a specification statement cannot appear in the executable section".)
C
      INTEGER NLOC, NRET, NARG
      CHARACTER*(4) CRESLT
      REAL ARG(NLOC,NARG), RET(NLOC,NRET)
      INTEGER IZ(*)
      CHARACTER CZ(*)*(1)
      DOUBLE PRECISION DZ(*)
      LOGICAL LZ(*)
      REAL RZ(*)
C
      INTEGER I, ICH, NCH
      REAL VIN(3), XN(3), VN(3), VT(3), VCH(3)
      REAL VDOTN, DPAR, NRPAR, DCH, NRCH
C
      REAL CPER, CPAR, RMODE, HALF
      PARAMETER (CPER  = 0.500)
      PARAMETER (CPAR  = 0.500)
      PARAMETER (RMODE = 1.0)
      PARAMETER (HALF  = 0.500)
C
C---- Outward normal of the film wall (flat floor, y = -0.005).
      XN(1) = 0.0
      XN(2) = 1.0
      XN(3) = 0.0
C
C---- Two children.  NCH is taken from the stack length so that the
C     routine still matches if max children is changed in the CCL.
      NCH = NRET / 7
C
      DO 5 I = 1, NRET
        RET(1,I) = 0.0
5     CONTINUE
      IF (NCH .LT. 2) THEN
        CRESLT = 'GOOD'
        RETURN
      ENDIF
C
      VIN(1) = ARG(1,1)
      VIN(2) = ARG(1,2)
      VIN(3) = ARG(1,3)
      DPAR   = ARG(1,4)
      NRPAR  = ARG(1,5)
C
C---- Split the impact velocity into wall-normal and wall-tangential
C     parts.  VN points INTO the wall for an incoming particle, so
C     -CPER*VN points back out of it.
      VDOTN = VIN(1)*XN(1) + VIN(2)*XN(2) + VIN(3)*XN(3)
      DO 10 I = 1, 3
        VN(I) = VDOTN * XN(I)
        VT(I) = VIN(I) - VN(I)
10    CONTINUE
C
C---- Two equal fragments, mass conserving: halving the diameter gives an
C     eighth of the mass each, so each carries four times the number rate
C     (2 * 4 * (1/8) = 1).
      DCH  = HALF * DPAR
      NRCH = 4.0 * NRPAR
C
      DO 20 I = 1, 3
        VCH(I) = CPAR*VT(I) - CPER*VN(I)
20    CONTINUE
C
      DO 30 ICH = 1, 2
        RET(1, ICH)           = 1.0
        RET(1, NCH + ICH)     = DCH
        RET(1, 2*NCH + ICH)   = NRCH
        RET(1, 3*NCH + 3*(ICH-1) + 1) = VCH(1)
        RET(1, 3*NCH + 3*(ICH-1) + 2) = VCH(2)
        RET(1, 3*NCH + 3*(ICH-1) + 3) = VCH(3)
        RET(1, 6*NCH + ICH)   = RMODE
30    CONTINUE
C
      CRESLT = 'GOOD'
C
      END
