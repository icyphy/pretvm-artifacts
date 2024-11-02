#ifndef SAT_ATTITUDE_CONTROLLER_H
#define SAT_ATTITUDE_CONTROLLER_H

typedef struct {
  int x;
  int y;
  int z;
} IntVec3;

// Fixed point confuguration
#define FIXED_POINT_FRACTION_BITS 12
#define FIXED_POINT_SCALE (1 << FIXED_POINT_FRACTION_BITS)

void gyro_reaction(IntVec3 *sample_ret);
void acc_reaction(IntVec3 *sample_ret);
void controller_run_reaction(IntVec3 *gyro_sample, IntVec3 *acc_sample,
                             IntVec3 *desired_angle, IntVec3 *last_error,
                             IntVec3 *error_accumulated, int Kp, int Ki, int Kd,
                             IntVec3 *motor_ret);
void controller_startup_reaction(float Kp, float Ki, float Kd, int *Kp_fixed,
                                 int *Ki_fixed, int *Kd_fixed);

void controller_user_input_reaction(IntVec3 *user_input,
                                    IntVec3 *desired_angle);

void motor_reaction(IntVec3 *control_signal);

void user_input_startup(IntVec3 *desired_angle);

#endif