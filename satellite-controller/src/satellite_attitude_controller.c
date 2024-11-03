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

void ars_reaction(IntVec3 *sample_ret) {
  static int i = 0;
  TAKE_TIME(200);
  sample_ret->x = synthetic_ars[i][0];
  sample_ret->y = synthetic_ars[i][1];
  sample_ret->x = synthetic_ars[i][2];
  if (i++ == NUM_ARS_SAMPLES) {
    i = 0;
  }
}
void sensor_fusion_startup_reaction(SensorFusionState *state) {
  state->last_gyro = (IntVec3){0, 0, 0};
  state->delta_t = 0.001 * FIXED_POINT_SCALE;
}

void sensor_fusion_reaction(SensorFusionState *state, IntVec3 *gyro,
                            IntVec3 *ars, IntVec3 *fusion_ret, int delta_t) {
  // Expected current_angle based on ARS data.
  IntVec3 ars_current_angle;
  ars_current_angle.x =
      state->last_gyro.x + (ars->x * delta_t) >> FIXED_POINT_FRACTION_BITS;
  ars_current_angle.y =
      state->last_gyro.y + (ars->y * delta_t) >> FIXED_POINT_FRACTION_BITS;
  ars_current_angle.z =
      state->last_gyro.z + (ars->z * delta_t) >> FIXED_POINT_FRACTION_BITS;

  // Do a weighted sum of the gyro and ARS data.
  fusion_ret->x = (gyro->x + ars_current_angle.x) >> 1;
  fusion_ret->y = (gyro->y + ars_current_angle.y) >> 1;
  fusion_ret->z = (gyro->z + ars_current_angle.z) >> 1;
}

void controller_run_reaction(ControllerState *state, IntVec3 *current_angle,
                             IntVec3 *motor_ret) {
  IntVec3 error;

  error.x = (current_angle->x - state->desired_angle.x);
  error.y = (current_angle->y - state->desired_angle.y);
  error.z = (current_angle->z - state->desired_angle.z);
  state->error_accumulated.x += error.x;
  state->error_accumulated.y += error.y;
  state->error_accumulated.z += error.z;

  motor_ret->x = ((state->Kp * error.x) >> FIXED_POINT_FRACTION_BITS) +
                 ((state->Ki * state->error_accumulated.x) >>
                  FIXED_POINT_FRACTION_BITS)  // integral component
                 + ((state->Kd * (state->last_error.x - error.x)) >>
                    FIXED_POINT_FRACTION_BITS);  // differential component
  motor_ret->y = ((state->Kp * error.y) >> FIXED_POINT_FRACTION_BITS) +
                 ((state->Ki * state->error_accumulated.y) >>
                  FIXED_POINT_FRACTION_BITS)  // integral component
                 + ((state->Kd * (state->last_error.y - error.y)) >>
                    FIXED_POINT_FRACTION_BITS);  // differential component
  motor_ret->z = ((state->Kp * error.z) >> FIXED_POINT_FRACTION_BITS) +
                 ((state->Ki * state->error_accumulated.z) >>
                  FIXED_POINT_FRACTION_BITS)  // integral component
                 + ((state->Kd * (state->last_error.z - error.z)) >>
                    FIXED_POINT_FRACTION_BITS);

  state->last_error.x = error.x;
  state->last_error.y = error.y;
  state->last_error.z = error.z;
}
void controller_startup_reaction(ControllerState *state, float Kp, float Ki,
                                 float Kd) {
  state->Kp = Kp * FIXED_POINT_SCALE;
  state->Ki = Ki * FIXED_POINT_SCALE;
  state->Kd = Kd * FIXED_POINT_SCALE;
}

void controller_user_input_reaction(ControllerState *state,
                                    IntVec3 *user_input) {
  state->desired_angle.x = user_input->x;
  state->desired_angle.y = user_input->y;
  state->desired_angle.z = user_input->z;
}

void motor_reaction(IntVec3 *control_signal) { TAKE_TIME(400); }

void user_input_startup(IntVec3 *desired_angle) {
  desired_angle->x = 4096;
  desired_angle->y = 2048;
  desired_angle->z = 819;
}