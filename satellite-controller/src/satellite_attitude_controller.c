#include "satellite_attitude_controller.h"
#include "synthetic_data.h"

// Convenience macro to simulate some execution time.
#define TAKE_TIME(N)              \
  do {                            \
    volatile int __x;             \
    for (int i = 0; i < N; i++) { \
      __x++;                      \
    }                             \
  } while (0)

void gyro_reaction(IntVec3 *sample_ret) {
  static int i = 0;

  TAKE_TIME(200);
  sample_ret->x = synthetic_gyro[i][0];
  sample_ret->y = synthetic_gyro[i][1];
  sample_ret->x = synthetic_gyro[i][2];
  if (i++ == NUM_GYRO_SAMPLES) {
    i = 0;
  }
}

void acc_reaction(IntVec3 *sample_ret) {
  static int i = 0;
  TAKE_TIME(200);
  sample_ret->x = synthetic_gyro[i][0];
  sample_ret->y = synthetic_gyro[i][1];
  sample_ret->x = synthetic_gyro[i][2];
  if (i++ == NUM_GYRO_SAMPLES) {
    i = 0;
  }
}

void controller_run_reaction(IntVec3 *current_angle, IntVec3 *current_speed,
                             IntVec3 *desired_angle, IntVec3 *last_error,
                             IntVec3 *error_accumulated, int Kp, int Ki, int Kd,
                             IntVec3 *motor_ret) {
  IntVec3 error;

  error.x = (current_angle->x - desired_angle->x);
  error.y = (current_angle->y - desired_angle->y);
  error.z = (current_angle->z - desired_angle->z);
  error_accumulated->x += error.x;
  error_accumulated->y += error.y;
  error_accumulated->z += error.z;

  motor_ret->x = ((Kp * error.x) >> FIXED_POINT_FRACTION_BITS) +
                 ((Ki * error_accumulated->x) >>
                  FIXED_POINT_FRACTION_BITS)  // integral component
                 + ((Kd * (last_error->x - error.x)) >>
                    FIXED_POINT_FRACTION_BITS);  // differential component
  motor_ret->y = ((Kp * error.y) >> FIXED_POINT_FRACTION_BITS) +
                 ((Ki * error_accumulated->y) >>
                  FIXED_POINT_FRACTION_BITS)  // integral component
                 + ((Kd * (last_error->y - error.y)) >>
                    FIXED_POINT_FRACTION_BITS);  // differential component
  motor_ret->z =
      ((Kp * error.z) >> FIXED_POINT_FRACTION_BITS) +
      ((Ki * error_accumulated->z) >>
       FIXED_POINT_FRACTION_BITS)  // integral component
      + ((Kd * (last_error->z - error.z)) >> FIXED_POINT_FRACTION_BITS);

  last_error->x = error.x;
  last_error->y = error.y;
  last_error->z = error.z;
}
void controller_startup_reaction(float Kp, float Ki, float Kd, int *Kp_fixed,
                                 int *Ki_fixed, int *Kd_fixed) {
  *Kp_fixed = Kp * FIXED_POINT_SCALE;
  *Ki_fixed = Ki * FIXED_POINT_SCALE;
  *Kd_fixed = Kd * FIXED_POINT_SCALE;
}

void controller_user_input_reaction(IntVec3 *user_input,
                                    IntVec3 *desired_angle) {
  desired_angle->x = user_input->x;
  desired_angle->y = user_input->y;
  desired_angle->z = user_input->z;
}

void motor_reaction(IntVec3 *control_signal) { TAKE_TIME(400); }

void user_input_startup(IntVec3 *desired_angle) {
  desired_angle->x = 4096;
  desired_angle->y = 2048;
  desired_angle->z = 819;
}