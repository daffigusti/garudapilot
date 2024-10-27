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
void err_fun(double *nom_x, double *delta_x, double *out_6726285173694629968) {
   out_6726285173694629968[0] = delta_x[0] + nom_x[0];
   out_6726285173694629968[1] = delta_x[1] + nom_x[1];
   out_6726285173694629968[2] = delta_x[2] + nom_x[2];
   out_6726285173694629968[3] = delta_x[3] + nom_x[3];
   out_6726285173694629968[4] = delta_x[4] + nom_x[4];
   out_6726285173694629968[5] = delta_x[5] + nom_x[5];
   out_6726285173694629968[6] = delta_x[6] + nom_x[6];
   out_6726285173694629968[7] = delta_x[7] + nom_x[7];
   out_6726285173694629968[8] = delta_x[8] + nom_x[8];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_7057348740940739273) {
   out_7057348740940739273[0] = -nom_x[0] + true_x[0];
   out_7057348740940739273[1] = -nom_x[1] + true_x[1];
   out_7057348740940739273[2] = -nom_x[2] + true_x[2];
   out_7057348740940739273[3] = -nom_x[3] + true_x[3];
   out_7057348740940739273[4] = -nom_x[4] + true_x[4];
   out_7057348740940739273[5] = -nom_x[5] + true_x[5];
   out_7057348740940739273[6] = -nom_x[6] + true_x[6];
   out_7057348740940739273[7] = -nom_x[7] + true_x[7];
   out_7057348740940739273[8] = -nom_x[8] + true_x[8];
}
void H_mod_fun(double *state, double *out_7362917196675134476) {
   out_7362917196675134476[0] = 1.0;
   out_7362917196675134476[1] = 0;
   out_7362917196675134476[2] = 0;
   out_7362917196675134476[3] = 0;
   out_7362917196675134476[4] = 0;
   out_7362917196675134476[5] = 0;
   out_7362917196675134476[6] = 0;
   out_7362917196675134476[7] = 0;
   out_7362917196675134476[8] = 0;
   out_7362917196675134476[9] = 0;
   out_7362917196675134476[10] = 1.0;
   out_7362917196675134476[11] = 0;
   out_7362917196675134476[12] = 0;
   out_7362917196675134476[13] = 0;
   out_7362917196675134476[14] = 0;
   out_7362917196675134476[15] = 0;
   out_7362917196675134476[16] = 0;
   out_7362917196675134476[17] = 0;
   out_7362917196675134476[18] = 0;
   out_7362917196675134476[19] = 0;
   out_7362917196675134476[20] = 1.0;
   out_7362917196675134476[21] = 0;
   out_7362917196675134476[22] = 0;
   out_7362917196675134476[23] = 0;
   out_7362917196675134476[24] = 0;
   out_7362917196675134476[25] = 0;
   out_7362917196675134476[26] = 0;
   out_7362917196675134476[27] = 0;
   out_7362917196675134476[28] = 0;
   out_7362917196675134476[29] = 0;
   out_7362917196675134476[30] = 1.0;
   out_7362917196675134476[31] = 0;
   out_7362917196675134476[32] = 0;
   out_7362917196675134476[33] = 0;
   out_7362917196675134476[34] = 0;
   out_7362917196675134476[35] = 0;
   out_7362917196675134476[36] = 0;
   out_7362917196675134476[37] = 0;
   out_7362917196675134476[38] = 0;
   out_7362917196675134476[39] = 0;
   out_7362917196675134476[40] = 1.0;
   out_7362917196675134476[41] = 0;
   out_7362917196675134476[42] = 0;
   out_7362917196675134476[43] = 0;
   out_7362917196675134476[44] = 0;
   out_7362917196675134476[45] = 0;
   out_7362917196675134476[46] = 0;
   out_7362917196675134476[47] = 0;
   out_7362917196675134476[48] = 0;
   out_7362917196675134476[49] = 0;
   out_7362917196675134476[50] = 1.0;
   out_7362917196675134476[51] = 0;
   out_7362917196675134476[52] = 0;
   out_7362917196675134476[53] = 0;
   out_7362917196675134476[54] = 0;
   out_7362917196675134476[55] = 0;
   out_7362917196675134476[56] = 0;
   out_7362917196675134476[57] = 0;
   out_7362917196675134476[58] = 0;
   out_7362917196675134476[59] = 0;
   out_7362917196675134476[60] = 1.0;
   out_7362917196675134476[61] = 0;
   out_7362917196675134476[62] = 0;
   out_7362917196675134476[63] = 0;
   out_7362917196675134476[64] = 0;
   out_7362917196675134476[65] = 0;
   out_7362917196675134476[66] = 0;
   out_7362917196675134476[67] = 0;
   out_7362917196675134476[68] = 0;
   out_7362917196675134476[69] = 0;
   out_7362917196675134476[70] = 1.0;
   out_7362917196675134476[71] = 0;
   out_7362917196675134476[72] = 0;
   out_7362917196675134476[73] = 0;
   out_7362917196675134476[74] = 0;
   out_7362917196675134476[75] = 0;
   out_7362917196675134476[76] = 0;
   out_7362917196675134476[77] = 0;
   out_7362917196675134476[78] = 0;
   out_7362917196675134476[79] = 0;
   out_7362917196675134476[80] = 1.0;
}
void f_fun(double *state, double dt, double *out_6645521087164499454) {
   out_6645521087164499454[0] = state[0];
   out_6645521087164499454[1] = state[1];
   out_6645521087164499454[2] = state[2];
   out_6645521087164499454[3] = state[3];
   out_6645521087164499454[4] = state[4];
   out_6645521087164499454[5] = dt*((-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]))*state[6] - 9.8000000000000007*state[8] + stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*state[1]) + (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*state[4])) + state[5];
   out_6645521087164499454[6] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*state[4])) + state[6];
   out_6645521087164499454[7] = state[7];
   out_6645521087164499454[8] = state[8];
}
void F_fun(double *state, double dt, double *out_5459025659633475373) {
   out_5459025659633475373[0] = 1;
   out_5459025659633475373[1] = 0;
   out_5459025659633475373[2] = 0;
   out_5459025659633475373[3] = 0;
   out_5459025659633475373[4] = 0;
   out_5459025659633475373[5] = 0;
   out_5459025659633475373[6] = 0;
   out_5459025659633475373[7] = 0;
   out_5459025659633475373[8] = 0;
   out_5459025659633475373[9] = 0;
   out_5459025659633475373[10] = 1;
   out_5459025659633475373[11] = 0;
   out_5459025659633475373[12] = 0;
   out_5459025659633475373[13] = 0;
   out_5459025659633475373[14] = 0;
   out_5459025659633475373[15] = 0;
   out_5459025659633475373[16] = 0;
   out_5459025659633475373[17] = 0;
   out_5459025659633475373[18] = 0;
   out_5459025659633475373[19] = 0;
   out_5459025659633475373[20] = 1;
   out_5459025659633475373[21] = 0;
   out_5459025659633475373[22] = 0;
   out_5459025659633475373[23] = 0;
   out_5459025659633475373[24] = 0;
   out_5459025659633475373[25] = 0;
   out_5459025659633475373[26] = 0;
   out_5459025659633475373[27] = 0;
   out_5459025659633475373[28] = 0;
   out_5459025659633475373[29] = 0;
   out_5459025659633475373[30] = 1;
   out_5459025659633475373[31] = 0;
   out_5459025659633475373[32] = 0;
   out_5459025659633475373[33] = 0;
   out_5459025659633475373[34] = 0;
   out_5459025659633475373[35] = 0;
   out_5459025659633475373[36] = 0;
   out_5459025659633475373[37] = 0;
   out_5459025659633475373[38] = 0;
   out_5459025659633475373[39] = 0;
   out_5459025659633475373[40] = 1;
   out_5459025659633475373[41] = 0;
   out_5459025659633475373[42] = 0;
   out_5459025659633475373[43] = 0;
   out_5459025659633475373[44] = 0;
   out_5459025659633475373[45] = dt*(stiffness_front*(-state[2] - state[3] + state[7])/(mass*state[1]) + (-stiffness_front - stiffness_rear)*state[5]/(mass*state[4]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[6]/(mass*state[4]));
   out_5459025659633475373[46] = -dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*pow(state[1], 2));
   out_5459025659633475373[47] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_5459025659633475373[48] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_5459025659633475373[49] = dt*((-1 - (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*pow(state[4], 2)))*state[6] - (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*pow(state[4], 2)));
   out_5459025659633475373[50] = dt*(-stiffness_front*state[0] - stiffness_rear*state[0])/(mass*state[4]) + 1;
   out_5459025659633475373[51] = dt*(-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]));
   out_5459025659633475373[52] = dt*stiffness_front*state[0]/(mass*state[1]);
   out_5459025659633475373[53] = -9.8000000000000007*dt;
   out_5459025659633475373[54] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front - pow(center_to_rear, 2)*stiffness_rear)*state[6]/(rotational_inertia*state[4]));
   out_5459025659633475373[55] = -center_to_front*dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*pow(state[1], 2));
   out_5459025659633475373[56] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_5459025659633475373[57] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_5459025659633475373[58] = dt*(-(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*pow(state[4], 2)) - (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*pow(state[4], 2)));
   out_5459025659633475373[59] = dt*(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(rotational_inertia*state[4]);
   out_5459025659633475373[60] = dt*(-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])/(rotational_inertia*state[4]) + 1;
   out_5459025659633475373[61] = center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_5459025659633475373[62] = 0;
   out_5459025659633475373[63] = 0;
   out_5459025659633475373[64] = 0;
   out_5459025659633475373[65] = 0;
   out_5459025659633475373[66] = 0;
   out_5459025659633475373[67] = 0;
   out_5459025659633475373[68] = 0;
   out_5459025659633475373[69] = 0;
   out_5459025659633475373[70] = 1;
   out_5459025659633475373[71] = 0;
   out_5459025659633475373[72] = 0;
   out_5459025659633475373[73] = 0;
   out_5459025659633475373[74] = 0;
   out_5459025659633475373[75] = 0;
   out_5459025659633475373[76] = 0;
   out_5459025659633475373[77] = 0;
   out_5459025659633475373[78] = 0;
   out_5459025659633475373[79] = 0;
   out_5459025659633475373[80] = 1;
}
void h_25(double *state, double *unused, double *out_4207101755320993023) {
   out_4207101755320993023[0] = state[6];
}
void H_25(double *state, double *unused, double *out_3227402766452543794) {
   out_3227402766452543794[0] = 0;
   out_3227402766452543794[1] = 0;
   out_3227402766452543794[2] = 0;
   out_3227402766452543794[3] = 0;
   out_3227402766452543794[4] = 0;
   out_3227402766452543794[5] = 0;
   out_3227402766452543794[6] = 1;
   out_3227402766452543794[7] = 0;
   out_3227402766452543794[8] = 0;
}
void h_24(double *state, double *unused, double *out_3608371447971603596) {
   out_3608371447971603596[0] = state[4];
   out_3608371447971603596[1] = state[5];
}
void H_24(double *state, double *unused, double *out_1498539647275229725) {
   out_1498539647275229725[0] = 0;
   out_1498539647275229725[1] = 0;
   out_1498539647275229725[2] = 0;
   out_1498539647275229725[3] = 0;
   out_1498539647275229725[4] = 1;
   out_1498539647275229725[5] = 0;
   out_1498539647275229725[6] = 0;
   out_1498539647275229725[7] = 0;
   out_1498539647275229725[8] = 0;
   out_1498539647275229725[9] = 0;
   out_1498539647275229725[10] = 0;
   out_1498539647275229725[11] = 0;
   out_1498539647275229725[12] = 0;
   out_1498539647275229725[13] = 0;
   out_1498539647275229725[14] = 1;
   out_1498539647275229725[15] = 0;
   out_1498539647275229725[16] = 0;
   out_1498539647275229725[17] = 0;
}
void h_30(double *state, double *unused, double *out_6032145572305651743) {
   out_6032145572305651743[0] = state[4];
}
void H_30(double *state, double *unused, double *out_8302650965765391067) {
   out_8302650965765391067[0] = 0;
   out_8302650965765391067[1] = 0;
   out_8302650965765391067[2] = 0;
   out_8302650965765391067[3] = 0;
   out_8302650965765391067[4] = 1;
   out_8302650965765391067[5] = 0;
   out_8302650965765391067[6] = 0;
   out_8302650965765391067[7] = 0;
   out_8302650965765391067[8] = 0;
}
void h_26(double *state, double *unused, double *out_8412316944939870092) {
   out_8412316944939870092[0] = state[7];
}
void H_26(double *state, double *unused, double *out_3884256830562855698) {
   out_3884256830562855698[0] = 0;
   out_3884256830562855698[1] = 0;
   out_3884256830562855698[2] = 0;
   out_3884256830562855698[3] = 0;
   out_3884256830562855698[4] = 0;
   out_3884256830562855698[5] = 0;
   out_3884256830562855698[6] = 0;
   out_3884256830562855698[7] = 1;
   out_3884256830562855698[8] = 0;
}
void h_27(double *state, double *unused, double *out_7236879614595492814) {
   out_7236879614595492814[0] = state[3];
}
void H_27(double *state, double *unused, double *out_7969329796143735638) {
   out_7969329796143735638[0] = 0;
   out_7969329796143735638[1] = 0;
   out_7969329796143735638[2] = 0;
   out_7969329796143735638[3] = 1;
   out_7969329796143735638[4] = 0;
   out_7969329796143735638[5] = 0;
   out_7969329796143735638[6] = 0;
   out_7969329796143735638[7] = 0;
   out_7969329796143735638[8] = 0;
}
void h_29(double *state, double *unused, double *out_6968693744480819819) {
   out_6968693744480819819[0] = state[1];
}
void H_29(double *state, double *unused, double *out_7792419621450998883) {
   out_7792419621450998883[0] = 0;
   out_7792419621450998883[1] = 1;
   out_7792419621450998883[2] = 0;
   out_7792419621450998883[3] = 0;
   out_7792419621450998883[4] = 0;
   out_7792419621450998883[5] = 0;
   out_7792419621450998883[6] = 0;
   out_7792419621450998883[7] = 0;
   out_7792419621450998883[8] = 0;
}
void h_28(double *state, double *unused, double *out_6208191191453213157) {
   out_6208191191453213157[0] = state[0];
}
void H_28(double *state, double *unused, double *out_5571925435189022159) {
   out_5571925435189022159[0] = 1;
   out_5571925435189022159[1] = 0;
   out_5571925435189022159[2] = 0;
   out_5571925435189022159[3] = 0;
   out_5571925435189022159[4] = 0;
   out_5571925435189022159[5] = 0;
   out_5571925435189022159[6] = 0;
   out_5571925435189022159[7] = 0;
   out_5571925435189022159[8] = 0;
}
void h_31(double *state, double *unused, double *out_3685837739563530336) {
   out_3685837739563530336[0] = state[8];
}
void H_31(double *state, double *unused, double *out_3258048728329504222) {
   out_3258048728329504222[0] = 0;
   out_3258048728329504222[1] = 0;
   out_3258048728329504222[2] = 0;
   out_3258048728329504222[3] = 0;
   out_3258048728329504222[4] = 0;
   out_3258048728329504222[5] = 0;
   out_3258048728329504222[6] = 0;
   out_3258048728329504222[7] = 0;
   out_3258048728329504222[8] = 1;
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
void car_err_fun(double *nom_x, double *delta_x, double *out_6726285173694629968) {
  err_fun(nom_x, delta_x, out_6726285173694629968);
}
void car_inv_err_fun(double *nom_x, double *true_x, double *out_7057348740940739273) {
  inv_err_fun(nom_x, true_x, out_7057348740940739273);
}
void car_H_mod_fun(double *state, double *out_7362917196675134476) {
  H_mod_fun(state, out_7362917196675134476);
}
void car_f_fun(double *state, double dt, double *out_6645521087164499454) {
  f_fun(state,  dt, out_6645521087164499454);
}
void car_F_fun(double *state, double dt, double *out_5459025659633475373) {
  F_fun(state,  dt, out_5459025659633475373);
}
void car_h_25(double *state, double *unused, double *out_4207101755320993023) {
  h_25(state, unused, out_4207101755320993023);
}
void car_H_25(double *state, double *unused, double *out_3227402766452543794) {
  H_25(state, unused, out_3227402766452543794);
}
void car_h_24(double *state, double *unused, double *out_3608371447971603596) {
  h_24(state, unused, out_3608371447971603596);
}
void car_H_24(double *state, double *unused, double *out_1498539647275229725) {
  H_24(state, unused, out_1498539647275229725);
}
void car_h_30(double *state, double *unused, double *out_6032145572305651743) {
  h_30(state, unused, out_6032145572305651743);
}
void car_H_30(double *state, double *unused, double *out_8302650965765391067) {
  H_30(state, unused, out_8302650965765391067);
}
void car_h_26(double *state, double *unused, double *out_8412316944939870092) {
  h_26(state, unused, out_8412316944939870092);
}
void car_H_26(double *state, double *unused, double *out_3884256830562855698) {
  H_26(state, unused, out_3884256830562855698);
}
void car_h_27(double *state, double *unused, double *out_7236879614595492814) {
  h_27(state, unused, out_7236879614595492814);
}
void car_H_27(double *state, double *unused, double *out_7969329796143735638) {
  H_27(state, unused, out_7969329796143735638);
}
void car_h_29(double *state, double *unused, double *out_6968693744480819819) {
  h_29(state, unused, out_6968693744480819819);
}
void car_H_29(double *state, double *unused, double *out_7792419621450998883) {
  H_29(state, unused, out_7792419621450998883);
}
void car_h_28(double *state, double *unused, double *out_6208191191453213157) {
  h_28(state, unused, out_6208191191453213157);
}
void car_H_28(double *state, double *unused, double *out_5571925435189022159) {
  H_28(state, unused, out_5571925435189022159);
}
void car_h_31(double *state, double *unused, double *out_3685837739563530336) {
  h_31(state, unused, out_3685837739563530336);
}
void car_H_31(double *state, double *unused, double *out_3258048728329504222) {
  H_31(state, unused, out_3258048728329504222);
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
