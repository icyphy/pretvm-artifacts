
/**
 * A static scheduler for the threaded runtime of the C target of Lingua Franca.
 *
 * @author{Shaokai Lin <shaokai@berkeley.edu>}
 */

#define REACTOR_LOCAL_TIME

#include <inttypes.h>
#include <assert.h>

#include "include/lf_types.h"
#include "include/tag.h"
#include "include/inst_lib.h"
#include "include/scheduler_instructions.h"

#ifndef TRACE_ALL_INSTRUCTIONS
#define TRACE_ALL_INSTRUCTIONS false
#endif
#define SPIN_WAIT_THRESHOLD SEC(1)

/////////////////// External Variables /////////////////////////
// Global variable defined in tag.c:
extern instant_t start_time;

// Global variables defined in schedule.c:
extern const inst_t* static_schedules[];
extern reg_t timeout;
extern const size_t num_counters;
extern reg_t time_offset;
extern reg_t offset_inc;
extern const uint64_t zero = 0;
extern volatile uint32_t counters[];
extern volatile reg_t return_addr[];
extern volatile reg_t binary_sema[];

/////////////////// Scheduler Private API /////////////////////////

/**
 * @brief The implementation of the ADD instruction
 */
void execute_inst_ADD(size_t worker_number, operand_t op1, operand_t op2, operand_t op3, bool debug, size_t* pc,
    reaction_t** returned_reaction, bool* exit_loop) {
    char* op_str = "ADD";
    LF_PRINT_DEBUG("*** Worker %zu executing instruction: [Line %zu] %s %" PRIu64 " %" PRIu64 " %" PRIu64, worker_number, *pc, op_str, op1.imm, op2.imm, op3.imm);
    reg_t *dst = op1.reg;
    reg_t *src = op2.reg;
    reg_t *src2 = op3.reg;
    *dst = *src + *src2;
    *pc += 1; // Increment pc.
}

/**
 * @brief The implementation of the ADDI instruction
 */
void execute_inst_ADDI(size_t worker_number, operand_t op1, operand_t op2, operand_t op3, bool debug, size_t* pc,
    reaction_t** returned_reaction, bool* exit_loop) {
    char* op_str = "ADDI";
    LF_PRINT_DEBUG("*** Worker %zu executing instruction: [Line %zu] %s %" PRIu64 " %" PRIu64 " %" PRIu64, worker_number, *pc, op_str, op1.imm, op2.imm, op3.imm);
    reg_t *dst = op1.reg;
    reg_t *src = op2.reg;
    // FIXME: Will there be problems if instant_t adds reg_t?
    *dst = *src + op3.imm;
    *pc += 1; // Increment pc.
}


/**
 * @brief The implementation of the BEQ instruction
 */
void execute_inst_BEQ(size_t worker_number, operand_t op1, operand_t op2, operand_t op3, bool debug, size_t* pc,
    reaction_t** returned_reaction, bool* exit_loop) {
    char* op_str = "BEQ";
    LF_PRINT_DEBUG("*** Worker %zu executing instruction: [Line %zu] %s %" PRIu64 " %" PRIu64 " %" PRIu64, worker_number, *pc, op_str, op1.imm, op2.imm, op3.imm);
    reg_t *_op1 = op1.reg;
    reg_t *_op2 = op2.reg;
    // These NULL checks allow _op1 and _op2 to be uninitialized in the static
    // schedule, which can save a few lines in the schedule. But it is debatable
    // whether this is good practice.
    if (_op1 != NULL && _op2 != NULL && *_op1 == *_op2) *pc = op3.imm;
    else *pc += 1;
}

/**
 * @brief The implementation of the BGE instruction
 */
void execute_inst_BGE(size_t worker_number, operand_t op1, operand_t op2, operand_t op3, bool debug, size_t* pc,
    reaction_t** returned_reaction, bool* exit_loop) {
    char* op_str = "BGE";
    LF_PRINT_DEBUG("*** Worker %zu executing instruction: [Line %zu] %s %" PRIu64 " %" PRIu64 " %" PRIu64, worker_number, *pc, op_str, op1.imm, op2.imm, op3.imm);
    reg_t *_op1 = op1.reg;
    reg_t *_op2 = op2.reg;
    LF_PRINT_DEBUG("Worker %zu: BGE : operand 1 = %lld, operand 2 = %lld", worker_number, *_op1, *_op2);
    if (_op1 != NULL && _op2 != NULL && *_op1 >= *_op2) *pc = op3.imm;
    else *pc += 1;
}

/**
 * @brief The implementation of the BLT instruction
 */
void execute_inst_BLT(size_t worker_number, operand_t op1, operand_t op2, operand_t op3, bool debug, size_t* pc,
    reaction_t** returned_reaction, bool* exit_loop) {
    char* op_str = "BLT";
    LF_PRINT_DEBUG("*** Worker %zu executing instruction: [Line %zu] %s %" PRIu64 " %" PRIu64 " %" PRIu64, worker_number, *pc, op_str, op1.imm, op2.imm, op3.imm);
    reg_t *_op1 = op1.reg;
    reg_t *_op2 = op2.reg;
    if (_op1 != NULL && _op2 != NULL && *_op1 < *_op2) *pc = op3.imm;
    else *pc += 1;
}

/**
 * @brief The implementation of the BNE instruction
 */
void execute_inst_BNE(size_t worker_number, operand_t op1, operand_t op2, operand_t op3, bool debug, size_t* pc,
    reaction_t** returned_reaction, bool* exit_loop) {
    char* op_str = "BNE";
    LF_PRINT_DEBUG("*** Worker %zu executing instruction: [Line %zu] %s %" PRIu64 " %" PRIu64 " %" PRIu64, worker_number, *pc, op_str, op1.imm, op2.imm, op3.imm);
    reg_t *_op1 = op1.reg;
    reg_t *_op2 = op2.reg;
    if (_op1 != NULL && _op2 != NULL && *_op1 != *_op2) *pc = op3.imm;
    else *pc += 1;
}

/**
 * @brief The implementation of the DU instruction
 */
void execute_inst_DU(size_t worker_number, operand_t op1, operand_t op2, operand_t op3, bool debug, size_t* pc,
    reaction_t** returned_reaction, bool* exit_loop) {
    char* op_str = "DU";
    LF_PRINT_DEBUG("*** Worker %zu executing instruction: [Line %zu] %s %" PRIu64 " %" PRIu64 " %" PRIu64, worker_number, *pc, op_str, op1.imm, op2.imm, op3.imm);
    // FIXME: There seems to be an overflow problem.
    // When wakeup_time overflows but lf_time_physical() doesn't,
    // _lf_interruptable_sleep_until_locked() terminates immediately.
    reg_t *src = op1.reg;
    instant_t current_time = lf_time_physical();
    instant_t wakeup_time = *src + op2.imm;
    LF_PRINT_DEBUG("DU wakeup time: %lld, base: %lld, offset: %lld", wakeup_time, *src, op2.imm);
    instant_t wait_interval = wakeup_time - current_time;
    // LF_PRINT_DEBUG("*** start_time: %lld, wakeup_time: %lld, op1: %lld, op2: %lld, current_physical_time: %lld\n", start_time, wakeup_time, *src, op2.imm, lf_time_physical());
    LF_PRINT_DEBUG("*** [Line %zu] Worker %zu delaying, current_physical_time: %lld, wakeup_time: %lld, wait_interval: %lld", *pc, worker_number, current_time, wakeup_time, wait_interval);
    if (wait_interval > 0) {
        // Approach 1: Only spin when the wait interval is less than SPIN_WAIT_THRESHOLD.
        if (wait_interval < SPIN_WAIT_THRESHOLD) {
            // Spin wait if the wait interval is less than 1 ms.
            //while (lf_time_physical() < wakeup_time);
        } else {
            // Otherwise sleep.
            //TODO: _lf_interruptable_sleep_until_locked(scheduler->env, wakeup_time);
        }
        // Approach 2: Spin wait.
        // while (lf_time_physical() < wakeup_time);
    }
    LF_PRINT_DEBUG("*** [Line %zu] Worker %zu done delaying", *pc, worker_number);
    *pc += 1; // Increment pc.
}

/**
 * @brief The implementation of the EXE instruction
 */
void execute_inst_EXE(size_t worker_number, operand_t op1, operand_t op2, operand_t op3, bool debug, size_t* pc,
    reaction_t** returned_reaction, bool* exit_loop) {
    char* op_str = "EXE";
    LF_PRINT_DEBUG("*** Worker %zu executing instruction: [Line %zu] %s %" PRIu64 " %" PRIu64 " %" PRIu64, worker_number, *pc, op_str, op1.imm, op2.imm, op3.imm);

    function_generic_t function = (function_generic_t)(uintptr_t)op1.reg;
    void *args = (void*)op2.reg;
    // Execute the function directly.
    LF_PRINT_DEBUG("*** [Line %zu] Worker %zu executing reaction", *pc, worker_number);
    //function(args);
    LF_PRINT_DEBUG("*** [Line %zu] Worker %zu done executing reaction", *pc, worker_number);
    *pc += 1; // Increment pc.
}


/**
 * @brief The implementation of the WLT instruction
 */
void execute_inst_WLT(size_t worker_number, operand_t op1, operand_t op2, operand_t op3, bool debug, size_t* pc,
    reaction_t** returned_reaction, bool* exit_loop) {
    char* op_str = "WLT";
    LF_PRINT_DEBUG("*** Worker %zu executing instruction: [Line %zu] %s %" PRIu64 " %" PRIu64 " %" PRIu64, worker_number, *pc, op_str, op1.imm, op2.imm, op3.imm);
    LF_PRINT_DEBUG("*** Worker %zu waiting", worker_number);
    reg_t *var = op1.reg;
    //while(*var >= op2.imm);
    LF_PRINT_DEBUG("*** Worker %zu done waiting", worker_number);
    *pc += 1; // Increment pc.
}

/**
 * @brief The implementation of the WU instruction
 */
void execute_inst_WU(size_t worker_number, operand_t op1, operand_t op2, operand_t op3, bool debug, size_t* pc,
    reaction_t** returned_reaction, bool* exit_loop) {
    char* op_str = "WU";
    LF_PRINT_DEBUG("*** Worker %zu executing instruction: [Line %zu] %s %" PRIu64 " %" PRIu64 " %" PRIu64, worker_number, *pc, op_str, op1.imm, op2.imm, op3.imm);
    LF_PRINT_DEBUG("*** Worker %zu waiting", worker_number);
    reg_t *var = op1.reg;
    //while(*var < op2.imm);
    LF_PRINT_DEBUG("*** Worker %zu done waiting", worker_number);
    *pc += 1; // Increment pc.
}

/**
 * @brief The implementation of the JAL instruction
 */
void execute_inst_JAL(size_t worker_number, operand_t op1, operand_t op2, operand_t op3, bool debug, size_t* pc,
    reaction_t** returned_reaction, bool* exit_loop) {
    char* op_str = "JAL";
    LF_PRINT_DEBUG("*** Worker %zu executing instruction: [Line %zu] %s %" PRIu64 " %" PRIu64 " %" PRIu64, worker_number, *pc, op_str, op1.imm, op2.imm, op3.imm);
    // Use the destination register as the return address and, if the
    // destination register is not the zero register, store pc+1 in it.
    reg_t *destReg = op1.reg;
    if (destReg != &zero) *destReg = *pc + 1;
    *pc = op2.imm + op3.imm; // New pc = label + offset
}

/**
 * @brief The implementation of the JALR instruction
 */
void execute_inst_JALR(size_t worker_number, operand_t op1, operand_t op2, operand_t op3, bool debug, size_t* pc,
    reaction_t** returned_reaction, bool* exit_loop) {
    char* op_str = "JALR";
    LF_PRINT_DEBUG("*** Worker %zu executing instruction: [Line %zu] %s %" PRIu64 " %" PRIu64 " %" PRIu64, worker_number, *pc, op_str, op1.imm, op2.imm, op3.imm);
    // Use the destination register as the return address and, if the
    // destination register is not the zero register, store pc+1 in it.
    reg_t *destReg = op1.reg;
    if (destReg != &zero) *destReg = *pc + 1;
    // Set pc to base addr + immediate.
    reg_t *baseAddr = op2.reg;
    *pc = *baseAddr + op3.imm;
}

/**
 * @brief The implementation of the STP instruction
 */
void execute_inst_STP(size_t worker_number, operand_t op1, operand_t op2, operand_t op3, bool debug, size_t* pc,
    reaction_t** returned_reaction, bool* exit_loop) {
    char* op_str = "STP";
    LF_PRINT_DEBUG("*** Worker %zu executing instruction: [Line %zu] %s %" PRIu64 " %" PRIu64 " %" PRIu64, worker_number, *pc, op_str, op1.imm, op2.imm, op3.imm);
    *exit_loop = true;
}
/**
 * @file
 * @author Edward A. Lee
 * @author Soroush Bateni
 * @author Hou Seng (Steven) Wong
 * @copyright (c) 2020-2023, The University of California at Berkeley
 * License in [BSD 2-clause](https://github.com/lf-lang/reactor-c/blob/main/LICENSE.md)
 * @brief Implementation of time and tag functions for Lingua Franca programs.
 */

#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>

#include "include/tag.h"
#include "include/lf_types.h"
#include "include/lf_types.h"
//#include "include/clock.h"

/**
 * An enum for specifying the desired tag when calling "lf_time"
 */
typedef enum _lf_time_type { LF_LOGICAL, LF_PHYSICAL, LF_ELAPSED_LOGICAL, LF_ELAPSED_PHYSICAL, LF_START } _lf_time_type;

//////////////// Global variables declared in tag.h:

// Global variables declared in tag.h:
instant_t start_time = NEVER;

////////////////  Functions declared in tag.

tag_t lf_tag(void* env) {
  //return ((environment_t*)env)->current_tag;
  tag_t tag;
  
  return tag;
}

instant_t lf_time_add(instant_t a, interval_t b) {
  if (a == NEVER || b == NEVER) {
    return NEVER;
  }
  if (a == FOREVER || b == FOREVER) {
    return FOREVER;
  }
  instant_t res = a + b;
  // Check for overflow
  if (res < a && b > 0) {
    return FOREVER;
  }
  // Check for underflow
  if (res > a && b < 0) {
    return NEVER;
  }
  return res;
}

tag_t lf_tag_add(tag_t a, tag_t b) {
  instant_t res = lf_time_add(a.time, b.time);
  if (res == FOREVER) {
    return FOREVER_TAG;
  }
  if (res == NEVER) {
    return NEVER_TAG;
  }

  if (b.time > 0) {
    // NOTE: The reason for handling this case is to "reset" the microstep counter at each after delay.
    a.microstep = 0; // Ignore microstep of first arg if time of second is > 0.
  }
  tag_t result = {.time = res, .microstep = a.microstep + b.microstep};

  // If microsteps overflows
  // FIXME: What should be the resulting tag in case of microstep overflow.
  //  see https://github.com/lf-lang/reactor-c/issues/430
  if (result.microstep < a.microstep) {
    return FOREVER_TAG;
  }
  return result;
}

int lf_tag_compare(tag_t tag1, tag_t tag2) {
  if (tag1.time < tag2.time) {
    return -1;
  } else if (tag1.time > tag2.time) {
    return 1;
  } else if (tag1.microstep < tag2.microstep) {
    return -1;
  } else if (tag1.microstep > tag2.microstep) {
    return 1;
  } else {
    return 0;
  }
}

tag_t lf_delay_tag(tag_t tag, interval_t interval) {
  if (tag.time == NEVER || interval < 0LL)
    return tag;
  // Note that overflow in C is undefined for signed variables.
  if (tag.time >= FOREVER - interval)
    return FOREVER_TAG; // Overflow.
  tag_t result = tag;
  if (interval == 0LL) {
    // Note that unsigned variables will wrap on overflow.
    // This is probably the only reasonable thing to do with overflowing
    // microsteps.
    result.microstep++;
  } else {
    result.time += interval;
    result.microstep = 0;
  }
  return result;
}

tag_t lf_delay_strict(tag_t tag, interval_t interval) {
  tag_t result = lf_delay_tag(tag, interval);
  if (interval != 0 && interval != NEVER && interval != FOREVER && result.time != NEVER && result.time != FOREVER) {
    result.time -= 1;
    result.microstep = UINT_MAX;
  }
  return result;
}

instant_t lf_time_logical(void* env) {
  //return ((environment_t*)env)->current_tag.time;
  return 0;
}

interval_t lf_time_logical_elapsed(void* env) { return lf_time_logical(env) - start_time; }

instant_t rdtime64() {
  return 0;
}

int lf_clock_gettime(instant_t* t) {
  *t = (instant_t)rdtime64();
  return 0;
}

instant_t lf_time_physical(void) {
  instant_t now;
  // Get the current clock value
  lf_clock_gettime(&now);
  return now;
}

instant_t lf_time_physical_elapsed(void) { return lf_time_physical() - start_time; }

instant_t lf_time_start(void) { return start_time; }

size_t lf_readable_time(char* buffer, instant_t time) {
  if (time <= (instant_t)0) {
    snprintf(buffer, 2, "0");
    return 1;
  }
  char* original_buffer = buffer;
  bool lead = false; // Set to true when first clause has been printed.
  if (time > WEEKS(1)) {
    lead = true;
    size_t printed = lf_comma_separated_time(buffer, time / WEEKS(1));
    time = time % WEEKS(1);
    buffer += printed;
    snprintf(buffer, 7, " weeks");
    buffer += 6;
  }
  if (time > DAYS(1)) {
    if (lead == true) {
      snprintf(buffer, 3, ", ");
      buffer += 2;
    }
    lead = true;
    size_t printed = lf_comma_separated_time(buffer, time / DAYS(1));
    time = time % DAYS(1);
    buffer += printed;
    snprintf(buffer, 3, " d");
    buffer += 2;
  }
  if (time > HOURS(1)) {
    if (lead == true) {
      snprintf(buffer, 3, ", ");
      buffer += 2;
    }
    lead = true;
    size_t printed = lf_comma_separated_time(buffer, time / HOURS(1));
    time = time % HOURS(1);
    buffer += printed;
    snprintf(buffer, 3, " h");
    buffer += 2;
  }
  if (time > MINUTES(1)) {
    if (lead == true) {
      snprintf(buffer, 3, ", ");
      buffer += 2;
    }
    lead = true;
    size_t printed = lf_comma_separated_time(buffer, time / MINUTES(1));
    time = time % MINUTES(1);
    buffer += printed;
    snprintf(buffer, 5, " min");
    buffer += 4;
  }
  if (time > SECONDS(1)) {
    if (lead == true) {
      snprintf(buffer, 3, ", ");
      buffer += 2;
    }
    lead = true;
    size_t printed = lf_comma_separated_time(buffer, time / SECONDS(1));
    time = time % SECONDS(1);
    buffer += printed;
    snprintf(buffer, 3, " s");
    buffer += 2;
  }
  if (time > (instant_t)0) {
    if (lead == true) {
      snprintf(buffer, 3, ", ");
      buffer += 2;
    }
    const char* units = "ns";
    if (time % MSEC(1) == (instant_t)0) {
      units = "ms";
      time = time / MSEC(1);
    } else if (time % USEC(1) == (instant_t)0) {
      units = "us";
      time = time / USEC(1);
    }
    size_t printed = lf_comma_separated_time(buffer, time);
    buffer += printed;
    snprintf(buffer, 4, " %s", units);
    buffer += strlen(units) + 1;
  }
  return (buffer - original_buffer);
}

size_t lf_comma_separated_time(char* buffer, instant_t time) {
  size_t result = 0; // The number of characters printed.
  // If the number is zero, print it and return.
  if (time == (instant_t)0) {
    snprintf(buffer, 2, "0");
    return 1;
  }
  // If the number is negative, print a minus sign.
  if (time < (instant_t)0) {
    snprintf(buffer, 2, "-");
    buffer++;
    result++;
  }
  int count = 0;
  // Assume the time value is no larger than 64 bits.
  instant_t clauses[7];
  while (time > (instant_t)0) {
    clauses[count++] = time;
    time = time / 1000;
  }
  // Highest order clause should not be filled with zeros.
  instant_t to_print = clauses[--count] % 1000;
  snprintf(buffer, 5, "%lld", (long long)to_print);
  if (to_print >= 100LL) {
    buffer += 3;
    result += 3;
  } else if (to_print >= 10LL) {
    buffer += 2;
    result += 2;
  } else {
    buffer += 1;
    result += 1;
  }
  while (count-- > 0) {
    to_print = clauses[count] % 1000LL;
    snprintf(buffer, 8, ",%03lld", (long long)to_print);
    buffer += 4;
    result += 4;
  }
  return result;
}
