#include "car.h"

namespace {
#define DIM 9
#define EDIM 9
#define MEDIM 9
typedef void (*Hfun)(double *, double *, double *);

double mass;

void set_mass(double x){ mass = x;}

double rotational_inertia;

void set_rotational_inertia(double x){ rotational_inertia = x;}

double center_to_front;

void set_center_to_front(double x){ center_to_front = x;}

double center_to_rear;

void set_center_to_rear(double x){ center_to_rear = x;}

double stiffness_front;

void set_stiffness_front(double x){ stiffness_front = x;}

double stiffness_rear;

void set_stiffness_rear(double x){ stiffness_rear = x;}
const static double MAHA_THRESH_25 = 3.8414588206941227;
const static double MAHA_THRESH_24 = 5.991464547107981;
const static double MAHA_THRESH_30 = 3.8414588206941227;
const static double MAHA_THRESH_26 = 3.8414588206941227;
const static double MAHA_THRESH_27 = 3.8414588206941227;
const static double MAHA_THRESH_29 = 3.8414588206941227;
const static double MAHA_THRESH_28 = 3.8414588206941227;
const static double MAHA_THRESH_31 = 3.8414588206941227;

/******************************************************************************
 *                       Code generated with SymPy 1.12                       *
 *                                                                            *
 *              See http://www.sympy.org/ for more information.               *
 *                                                                            *
 *                         This file is part of 'ekf'                         *
 ******************************************************************************/
void err_fun(double *nom_x, double *delta_x, double *out_4527700108585020532) {
   out_4527700108585020532[0] = delta_x[0] + nom_x[0];
   out_4527700108585020532[1] = delta_x[1] + nom_x[1];
   out_4527700108585020532[2] = delta_x[2] + nom_x[2];
   out_4527700108585020532[3] = delta_x[3] + nom_x[3];
   out_4527700108585020532[4] = delta_x[4] + nom_x[4];
   out_4527700108585020532[5] = delta_x[5] + nom_x[5];
   out_4527700108585020532[6] = delta_x[6] + nom_x[6];
   out_4527700108585020532[7] = delta_x[7] + nom_x[7];
   out_4527700108585020532[8] = delta_x[8] + nom_x[8];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_8425844027498184406) {
   out_8425844027498184406[0] = -nom_x[0] + true_x[0];
   out_8425844027498184406[1] = -nom_x[1] + true_x[1];
   out_8425844027498184406[2] = -nom_x[2] + true_x[2];
   out_8425844027498184406[3] = -nom_x[3] + true_x[3];
   out_8425844027498184406[4] = -nom_x[4] + true_x[4];
   out_8425844027498184406[5] = -nom_x[5] + true_x[5];
   out_8425844027498184406[6] = -nom_x[6] + true_x[6];
   out_8425844027498184406[7] = -nom_x[7] + true_x[7];
   out_8425844027498184406[8] = -nom_x[8] + true_x[8];
}
void H_mod_fun(double *state, double *out_7826352841266005226) {
   out_7826352841266005226[0] = 1.0;
   out_7826352841266005226[1] = 0;
   out_7826352841266005226[2] = 0;
   out_7826352841266005226[3] = 0;
   out_7826352841266005226[4] = 0;
   out_7826352841266005226[5] = 0;
   out_7826352841266005226[6] = 0;
   out_7826352841266005226[7] = 0;
   out_7826352841266005226[8] = 0;
   out_7826352841266005226[9] = 0;
   out_7826352841266005226[10] = 1.0;
   out_7826352841266005226[11] = 0;
   out_7826352841266005226[12] = 0;
   out_7826352841266005226[13] = 0;
   out_7826352841266005226[14] = 0;
   out_7826352841266005226[15] = 0;
   out_7826352841266005226[16] = 0;
   out_7826352841266005226[17] = 0;
   out_7826352841266005226[18] = 0;
   out_7826352841266005226[19] = 0;
   out_7826352841266005226[20] = 1.0;
   out_7826352841266005226[21] = 0;
   out_7826352841266005226[22] = 0;
   out_7826352841266005226[23] = 0;
   out_7826352841266005226[24] = 0;
   out_7826352841266005226[25] = 0;
   out_7826352841266005226[26] = 0;
   out_7826352841266005226[27] = 0;
   out_7826352841266005226[28] = 0;
   out_7826352841266005226[29] = 0;
   out_7826352841266005226[30] = 1.0;
   out_7826352841266005226[31] = 0;
   out_7826352841266005226[32] = 0;
   out_7826352841266005226[33] = 0;
   out_7826352841266005226[34] = 0;
   out_7826352841266005226[35] = 0;
   out_7826352841266005226[36] = 0;
   out_7826352841266005226[37] = 0;
   out_7826352841266005226[38] = 0;
   out_7826352841266005226[39] = 0;
   out_7826352841266005226[40] = 1.0;
   out_7826352841266005226[41] = 0;
   out_7826352841266005226[42] = 0;
   out_7826352841266005226[43] = 0;
   out_7826352841266005226[44] = 0;
   out_7826352841266005226[45] = 0;
   out_7826352841266005226[46] = 0;
   out_7826352841266005226[47] = 0;
   out_7826352841266005226[48] = 0;
   out_7826352841266005226[49] = 0;
   out_7826352841266005226[50] = 1.0;
   out_7826352841266005226[51] = 0;
   out_7826352841266005226[52] = 0;
   out_7826352841266005226[53] = 0;
   out_7826352841266005226[54] = 0;
   out_7826352841266005226[55] = 0;
   out_7826352841266005226[56] = 0;
   out_7826352841266005226[57] = 0;
   out_7826352841266005226[58] = 0;
   out_7826352841266005226[59] = 0;
   out_7826352841266005226[60] = 1.0;
   out_7826352841266005226[61] = 0;
   out_7826352841266005226[62] = 0;
   out_7826352841266005226[63] = 0;
   out_7826352841266005226[64] = 0;
   out_7826352841266005226[65] = 0;
   out_7826352841266005226[66] = 0;
   out_7826352841266005226[67] = 0;
   out_7826352841266005226[68] = 0;
   out_7826352841266005226[69] = 0;
   out_7826352841266005226[70] = 1.0;
   out_7826352841266005226[71] = 0;
   out_7826352841266005226[72] = 0;
   out_7826352841266005226[73] = 0;
   out_7826352841266005226[74] = 0;
   out_7826352841266005226[75] = 0;
   out_7826352841266005226[76] = 0;
   out_7826352841266005226[77] = 0;
   out_7826352841266005226[78] = 0;
   out_7826352841266005226[79] = 0;
   out_7826352841266005226[80] = 1.0;
}
void f_fun(double *state, double dt, double *out_8964308674945905457) {
   out_8964308674945905457[0] = state[0];
   out_8964308674945905457[1] = state[1];
   out_8964308674945905457[2] = state[2];
   out_8964308674945905457[3] = state[3];
   out_8964308674945905457[4] = state[4];
   out_8964308674945905457[5] = dt*((-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]))*state[6] - 9.8000000000000007*state[8] + stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*state[1]) + (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*state[4])) + state[5];
   out_8964308674945905457[6] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*state[4])) + state[6];
   out_8964308674945905457[7] = state[7];
   out_8964308674945905457[8] = state[8];
}
void F_fun(double *state, double dt, double *out_5832112231889200908) {
   out_5832112231889200908[0] = 1;
   out_5832112231889200908[1] = 0;
   out_5832112231889200908[2] = 0;
   out_5832112231889200908[3] = 0;
   out_5832112231889200908[4] = 0;
   out_5832112231889200908[5] = 0;
   out_5832112231889200908[6] = 0;
   out_5832112231889200908[7] = 0;
   out_5832112231889200908[8] = 0;
   out_5832112231889200908[9] = 0;
   out_5832112231889200908[10] = 1;
   out_5832112231889200908[11] = 0;
   out_5832112231889200908[12] = 0;
   out_5832112231889200908[13] = 0;
   out_5832112231889200908[14] = 0;
   out_5832112231889200908[15] = 0;
   out_5832112231889200908[16] = 0;
   out_5832112231889200908[17] = 0;
   out_5832112231889200908[18] = 0;
   out_5832112231889200908[19] = 0;
   out_5832112231889200908[20] = 1;
   out_5832112231889200908[21] = 0;
   out_5832112231889200908[22] = 0;
   out_5832112231889200908[23] = 0;
   out_5832112231889200908[24] = 0;
   out_5832112231889200908[25] = 0;
   out_5832112231889200908[26] = 0;
   out_5832112231889200908[27] = 0;
   out_5832112231889200908[28] = 0;
   out_5832112231889200908[29] = 0;
   out_5832112231889200908[30] = 1;
   out_5832112231889200908[31] = 0;
   out_5832112231889200908[32] = 0;
   out_5832112231889200908[33] = 0;
   out_5832112231889200908[34] = 0;
   out_5832112231889200908[35] = 0;
   out_5832112231889200908[36] = 0;
   out_5832112231889200908[37] = 0;
   out_5832112231889200908[38] = 0;
   out_5832112231889200908[39] = 0;
   out_5832112231889200908[40] = 1;
   out_5832112231889200908[41] = 0;
   out_5832112231889200908[42] = 0;
   out_5832112231889200908[43] = 0;
   out_5832112231889200908[44] = 0;
   out_5832112231889200908[45] = dt*(stiffness_front*(-state[2] - state[3] + state[7])/(mass*state[1]) + (-stiffness_front - stiffness_rear)*state[5]/(mass*state[4]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[6]/(mass*state[4]));
   out_5832112231889200908[46] = -dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*pow(state[1], 2));
   out_5832112231889200908[47] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_5832112231889200908[48] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_5832112231889200908[49] = dt*((-1 - (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*pow(state[4], 2)))*state[6] - (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*pow(state[4], 2)));
   out_5832112231889200908[50] = dt*(-stiffness_front*state[0] - stiffness_rear*state[0])/(mass*state[4]) + 1;
   out_5832112231889200908[51] = dt*(-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]));
   out_5832112231889200908[52] = dt*stiffness_front*state[0]/(mass*state[1]);
   out_5832112231889200908[53] = -9.8000000000000007*dt;
   out_5832112231889200908[54] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front - pow(center_to_rear, 2)*stiffness_rear)*state[6]/(rotational_inertia*state[4]));
   out_5832112231889200908[55] = -center_to_front*dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*pow(state[1], 2));
   out_5832112231889200908[56] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_5832112231889200908[57] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_5832112231889200908[58] = dt*(-(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*pow(state[4], 2)) - (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*pow(state[4], 2)));
   out_5832112231889200908[59] = dt*(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(rotational_inertia*state[4]);
   out_5832112231889200908[60] = dt*(-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])/(rotational_inertia*state[4]) + 1;
   out_5832112231889200908[61] = center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_5832112231889200908[62] = 0;
   out_5832112231889200908[63] = 0;
   out_5832112231889200908[64] = 0;
   out_5832112231889200908[65] = 0;
   out_5832112231889200908[66] = 0;
   out_5832112231889200908[67] = 0;
   out_5832112231889200908[68] = 0;
   out_5832112231889200908[69] = 0;
   out_5832112231889200908[70] = 1;
   out_5832112231889200908[71] = 0;
   out_5832112231889200908[72] = 0;
   out_5832112231889200908[73] = 0;
   out_5832112231889200908[74] = 0;
   out_5832112231889200908[75] = 0;
   out_5832112231889200908[76] = 0;
   out_5832112231889200908[77] = 0;
   out_5832112231889200908[78] = 0;
   out_5832112231889200908[79] = 0;
   out_5832112231889200908[80] = 1;
}
void h_25(double *state, double *unused, double *out_8013206829090437003) {
   out_8013206829090437003[0] = state[6];
}
void H_25(double *state, double *unused, double *out_1985456661780743497) {
   out_1985456661780743497[0] = 0;
   out_1985456661780743497[1] = 0;
   out_1985456661780743497[2] = 0;
   out_1985456661780743497[3] = 0;
   out_1985456661780743497[4] = 0;
   out_1985456661780743497[5] = 0;
   out_1985456661780743497[6] = 1;
   out_1985456661780743497[7] = 0;
   out_1985456661780743497[8] = 0;
}
void h_24(double *state, double *unused, double *out_3541855382808878600) {
   out_3541855382808878600[0] = state[4];
   out_3541855382808878600[1] = state[5];
}
void H_24(double *state, double *unused, double *out_572428413742334660) {
   out_572428413742334660[0] = 0;
   out_572428413742334660[1] = 0;
   out_572428413742334660[2] = 0;
   out_572428413742334660[3] = 0;
   out_572428413742334660[4] = 1;
   out_572428413742334660[5] = 0;
   out_572428413742334660[6] = 0;
   out_572428413742334660[7] = 0;
   out_572428413742334660[8] = 0;
   out_572428413742334660[9] = 0;
   out_572428413742334660[10] = 0;
   out_572428413742334660[11] = 0;
   out_572428413742334660[12] = 0;
   out_572428413742334660[13] = 0;
   out_572428413742334660[14] = 1;
   out_572428413742334660[15] = 0;
   out_572428413742334660[16] = 0;
   out_572428413742334660[17] = 0;
}
void h_30(double *state, double *unused, double *out_249941572269764562) {
   out_249941572269764562[0] = state[4];
}
void H_30(double *state, double *unused, double *out_532876296726505130) {
   out_532876296726505130[0] = 0;
   out_532876296726505130[1] = 0;
   out_532876296726505130[2] = 0;
   out_532876296726505130[3] = 0;
   out_532876296726505130[4] = 1;
   out_532876296726505130[5] = 0;
   out_532876296726505130[6] = 0;
   out_532876296726505130[7] = 0;
   out_532876296726505130[8] = 0;
}
void h_26(double *state, double *unused, double *out_6648983089683613708) {
   out_6648983089683613708[0] = state[7];
}
void H_26(double *state, double *unused, double *out_5726959980654799721) {
   out_5726959980654799721[0] = 0;
   out_5726959980654799721[1] = 0;
   out_5726959980654799721[2] = 0;
   out_5726959980654799721[3] = 0;
   out_5726959980654799721[4] = 0;
   out_5726959980654799721[5] = 0;
   out_5726959980654799721[6] = 0;
   out_5726959980654799721[7] = 1;
   out_5726959980654799721[8] = 0;
}
void h_27(double *state, double *unused, double *out_4976420777646104318) {
   out_4976420777646104318[0] = state[3];
}
void H_27(double *state, double *unused, double *out_1641887015073919781) {
   out_1641887015073919781[0] = 0;
   out_1641887015073919781[1] = 0;
   out_1641887015073919781[2] = 0;
   out_1641887015073919781[3] = 1;
   out_1641887015073919781[4] = 0;
   out_1641887015073919781[5] = 0;
   out_1641887015073919781[6] = 0;
   out_1641887015073919781[7] = 0;
   out_1641887015073919781[8] = 0;
}
void h_29(double *state, double *unused, double *out_5251614839930610207) {
   out_5251614839930610207[0] = state[1];
}
void H_29(double *state, double *unused, double *out_1043107641040897314) {
   out_1043107641040897314[0] = 0;
   out_1043107641040897314[1] = 1;
   out_1043107641040897314[2] = 0;
   out_1043107641040897314[3] = 0;
   out_1043107641040897314[4] = 0;
   out_1043107641040897314[5] = 0;
   out_1043107641040897314[6] = 0;
   out_1043107641040897314[7] = 0;
   out_1043107641040897314[8] = 0;
}
void h_28(double *state, double *unused, double *out_365446458239926245) {
   out_365446458239926245[0] = state[0];
}
void H_28(double *state, double *unused, double *out_4039291376028633260) {
   out_4039291376028633260[0] = 1;
   out_4039291376028633260[1] = 0;
   out_4039291376028633260[2] = 0;
   out_4039291376028633260[3] = 0;
   out_4039291376028633260[4] = 0;
   out_4039291376028633260[5] = 0;
   out_4039291376028633260[6] = 0;
   out_4039291376028633260[7] = 0;
   out_4039291376028633260[8] = 0;
}
void h_31(double *state, double *unused, double *out_7867687004869782032) {
   out_7867687004869782032[0] = state[8];
}
void H_31(double *state, double *unused, double *out_6353168082888151197) {
   out_6353168082888151197[0] = 0;
   out_6353168082888151197[1] = 0;
   out_6353168082888151197[2] = 0;
   out_6353168082888151197[3] = 0;
   out_6353168082888151197[4] = 0;
   out_6353168082888151197[5] = 0;
   out_6353168082888151197[6] = 0;
   out_6353168082888151197[7] = 0;
   out_6353168082888151197[8] = 1;
}
#include <eigen3/Eigen/Dense>
#include <iostream>

typedef Eigen::Matrix<double, DIM, DIM, Eigen::RowMajor> DDM;
typedef Eigen::Matrix<double, EDIM, EDIM, Eigen::RowMajor> EEM;
typedef Eigen::Matrix<double, DIM, EDIM, Eigen::RowMajor> DEM;

void predict(double *in_x, double *in_P, double *in_Q, double dt) {
  typedef Eigen::Matrix<double, MEDIM, MEDIM, Eigen::RowMajor> RRM;

  double nx[DIM] = {0};
  double in_F[EDIM*EDIM] = {0};

  // functions from sympy
  f_fun(in_x, dt, nx);
  F_fun(in_x, dt, in_F);


  EEM F(in_F);
  EEM P(in_P);
  EEM Q(in_Q);

  RRM F_main = F.topLeftCorner(MEDIM, MEDIM);
  P.topLeftCorner(MEDIM, MEDIM) = (F_main * P.topLeftCorner(MEDIM, MEDIM)) * F_main.transpose();
  P.topRightCorner(MEDIM, EDIM - MEDIM) = F_main * P.topRightCorner(MEDIM, EDIM - MEDIM);
  P.bottomLeftCorner(EDIM - MEDIM, MEDIM) = P.bottomLeftCorner(EDIM - MEDIM, MEDIM) * F_main.transpose();

  P = P + dt*Q;

  // copy out state
  memcpy(in_x, nx, DIM * sizeof(double));
  memcpy(in_P, P.data(), EDIM * EDIM * sizeof(double));
}

// note: extra_args dim only correct when null space projecting
// otherwise 1
template <int ZDIM, int EADIM, bool MAHA_TEST>
void update(double *in_x, double *in_P, Hfun h_fun, Hfun H_fun, Hfun Hea_fun, double *in_z, double *in_R, double *in_ea, double MAHA_THRESHOLD) {
  typedef Eigen::Matrix<double, ZDIM, ZDIM, Eigen::RowMajor> ZZM;
  typedef Eigen::Matrix<double, ZDIM, DIM, Eigen::RowMajor> ZDM;
  typedef Eigen::Matrix<double, Eigen::Dynamic, EDIM, Eigen::RowMajor> XEM;
  //typedef Eigen::Matrix<double, EDIM, ZDIM, Eigen::RowMajor> EZM;
  typedef Eigen::Matrix<double, Eigen::Dynamic, 1> X1M;
  typedef Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> XXM;

  double in_hx[ZDIM] = {0};
  double in_H[ZDIM * DIM] = {0};
  double in_H_mod[EDIM * DIM] = {0};
  double delta_x[EDIM] = {0};
  double x_new[DIM] = {0};


  // state x, P
  Eigen::Matrix<double, ZDIM, 1> z(in_z);
  EEM P(in_P);
  ZZM pre_R(in_R);

  // functions from sympy
  h_fun(in_x, in_ea, in_hx);
  H_fun(in_x, in_ea, in_H);
  ZDM pre_H(in_H);

  // get y (y = z - hx)
  Eigen::Matrix<double, ZDIM, 1> pre_y(in_hx); pre_y = z - pre_y;
  X1M y; XXM H; XXM R;
  if (Hea_fun){
    typedef Eigen::Matrix<double, ZDIM, EADIM, Eigen::RowMajor> ZAM;
    double in_Hea[ZDIM * EADIM] = {0};
    Hea_fun(in_x, in_ea, in_Hea);
    ZAM Hea(in_Hea);
    XXM A = Hea.transpose().fullPivLu().kernel();


    y = A.transpose() * pre_y;
    H = A.transpose() * pre_H;
    R = A.transpose() * pre_R * A;
  } else {
    y = pre_y;
    H = pre_H;
    R = pre_R;
  }
  // get modified H
  H_mod_fun(in_x, in_H_mod);
  DEM H_mod(in_H_mod);
  XEM H_err = H * H_mod;

  // Do mahalobis distance test
  if (MAHA_TEST){
    XXM a = (H_err * P * H_err.transpose() + R).inverse();
    double maha_dist = y.transpose() * a * y;
    if (maha_dist > MAHA_THRESHOLD){
      R = 1.0e16 * R;
    }
  }

  // Outlier resilient weighting
  double weight = 1;//(1.5)/(1 + y.squaredNorm()/R.sum());

  // kalman gains and I_KH
  XXM S = ((H_err * P) * H_err.transpose()) + R/weight;
  XEM KT = S.fullPivLu().solve(H_err * P.transpose());
  //EZM K = KT.transpose(); TODO: WHY DOES THIS NOT COMPILE?
  //EZM K = S.fullPivLu().solve(H_err * P.transpose()).transpose();
  //std::cout << "Here is the matrix rot:\n" << K << std::endl;
  EEM I_KH = Eigen::Matrix<double, EDIM, EDIM>::Identity() - (KT.transpose() * H_err);

  // update state by injecting dx
  Eigen::Matrix<double, EDIM, 1> dx(delta_x);
  dx  = (KT.transpose() * y);
  memcpy(delta_x, dx.data(), EDIM * sizeof(double));
  err_fun(in_x, delta_x, x_new);
  Eigen::Matrix<double, DIM, 1> x(x_new);

  // update cov
  P = ((I_KH * P) * I_KH.transpose()) + ((KT.transpose() * R) * KT);

  // copy out state
  memcpy(in_x, x.data(), DIM * sizeof(double));
  memcpy(in_P, P.data(), EDIM * EDIM * sizeof(double));
  memcpy(in_z, y.data(), y.rows() * sizeof(double));
}




}
extern "C" {

void car_update_25(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_25, H_25, NULL, in_z, in_R, in_ea, MAHA_THRESH_25);
}
void car_update_24(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<2, 3, 0>(in_x, in_P, h_24, H_24, NULL, in_z, in_R, in_ea, MAHA_THRESH_24);
}
void car_update_30(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_30, H_30, NULL, in_z, in_R, in_ea, MAHA_THRESH_30);
}
void car_update_26(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_26, H_26, NULL, in_z, in_R, in_ea, MAHA_THRESH_26);
}
void car_update_27(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_27, H_27, NULL, in_z, in_R, in_ea, MAHA_THRESH_27);
}
void car_update_29(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_29, H_29, NULL, in_z, in_R, in_ea, MAHA_THRESH_29);
}
void car_update_28(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_28, H_28, NULL, in_z, in_R, in_ea, MAHA_THRESH_28);
}
void car_update_31(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_31, H_31, NULL, in_z, in_R, in_ea, MAHA_THRESH_31);
}
void car_err_fun(double *nom_x, double *delta_x, double *out_4527700108585020532) {
  err_fun(nom_x, delta_x, out_4527700108585020532);
}
void car_inv_err_fun(double *nom_x, double *true_x, double *out_8425844027498184406) {
  inv_err_fun(nom_x, true_x, out_8425844027498184406);
}
void car_H_mod_fun(double *state, double *out_7826352841266005226) {
  H_mod_fun(state, out_7826352841266005226);
}
void car_f_fun(double *state, double dt, double *out_8964308674945905457) {
  f_fun(state,  dt, out_8964308674945905457);
}
void car_F_fun(double *state, double dt, double *out_5832112231889200908) {
  F_fun(state,  dt, out_5832112231889200908);
}
void car_h_25(double *state, double *unused, double *out_8013206829090437003) {
  h_25(state, unused, out_8013206829090437003);
}
void car_H_25(double *state, double *unused, double *out_1985456661780743497) {
  H_25(state, unused, out_1985456661780743497);
}
void car_h_24(double *state, double *unused, double *out_3541855382808878600) {
  h_24(state, unused, out_3541855382808878600);
}
void car_H_24(double *state, double *unused, double *out_572428413742334660) {
  H_24(state, unused, out_572428413742334660);
}
void car_h_30(double *state, double *unused, double *out_249941572269764562) {
  h_30(state, unused, out_249941572269764562);
}
void car_H_30(double *state, double *unused, double *out_532876296726505130) {
  H_30(state, unused, out_532876296726505130);
}
void car_h_26(double *state, double *unused, double *out_6648983089683613708) {
  h_26(state, unused, out_6648983089683613708);
}
void car_H_26(double *state, double *unused, double *out_5726959980654799721) {
  H_26(state, unused, out_5726959980654799721);
}
void car_h_27(double *state, double *unused, double *out_4976420777646104318) {
  h_27(state, unused, out_4976420777646104318);
}
void car_H_27(double *state, double *unused, double *out_1641887015073919781) {
  H_27(state, unused, out_1641887015073919781);
}
void car_h_29(double *state, double *unused, double *out_5251614839930610207) {
  h_29(state, unused, out_5251614839930610207);
}
void car_H_29(double *state, double *unused, double *out_1043107641040897314) {
  H_29(state, unused, out_1043107641040897314);
}
void car_h_28(double *state, double *unused, double *out_365446458239926245) {
  h_28(state, unused, out_365446458239926245);
}
void car_H_28(double *state, double *unused, double *out_4039291376028633260) {
  H_28(state, unused, out_4039291376028633260);
}
void car_h_31(double *state, double *unused, double *out_7867687004869782032) {
  h_31(state, unused, out_7867687004869782032);
}
void car_H_31(double *state, double *unused, double *out_6353168082888151197) {
  H_31(state, unused, out_6353168082888151197);
}
void car_predict(double *in_x, double *in_P, double *in_Q, double dt) {
  predict(in_x, in_P, in_Q, dt);
}
void car_set_mass(double x) {
  set_mass(x);
}
void car_set_rotational_inertia(double x) {
  set_rotational_inertia(x);
}
void car_set_center_to_front(double x) {
  set_center_to_front(x);
}
void car_set_center_to_rear(double x) {
  set_center_to_rear(x);
}
void car_set_stiffness_front(double x) {
  set_stiffness_front(x);
}
void car_set_stiffness_rear(double x) {
  set_stiffness_rear(x);
}
}

const EKF car = {
  .name = "car",
  .kinds = { 25, 24, 30, 26, 27, 29, 28, 31 },
  .feature_kinds = {  },
  .f_fun = car_f_fun,
  .F_fun = car_F_fun,
  .err_fun = car_err_fun,
  .inv_err_fun = car_inv_err_fun,
  .H_mod_fun = car_H_mod_fun,
  .predict = car_predict,
  .hs = {
    { 25, car_h_25 },
    { 24, car_h_24 },
    { 30, car_h_30 },
    { 26, car_h_26 },
    { 27, car_h_27 },
    { 29, car_h_29 },
    { 28, car_h_28 },
    { 31, car_h_31 },
  },
  .Hs = {
    { 25, car_H_25 },
    { 24, car_H_24 },
    { 30, car_H_30 },
    { 26, car_H_26 },
    { 27, car_H_27 },
    { 29, car_H_29 },
    { 28, car_H_28 },
    { 31, car_H_31 },
  },
  .updates = {
    { 25, car_update_25 },
    { 24, car_update_24 },
    { 30, car_update_30 },
    { 26, car_update_26 },
    { 27, car_update_27 },
    { 29, car_update_29 },
    { 28, car_update_28 },
    { 31, car_update_31 },
  },
  .Hes = {
  },
  .sets = {
    { "mass", car_set_mass },
    { "rotational_inertia", car_set_rotational_inertia },
    { "center_to_front", car_set_center_to_front },
    { "center_to_rear", car_set_center_to_rear },
    { "stiffness_front", car_set_stiffness_front },
    { "stiffness_rear", car_set_stiffness_rear },
  },
  .extra_routines = {
  },
};

ekf_lib_init(car)
