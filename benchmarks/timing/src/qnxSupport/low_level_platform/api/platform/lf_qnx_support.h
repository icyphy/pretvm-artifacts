/**
 * @file lf_qnx_support.h
 * @brief QNX-specific platform support for the Lingua Franca runtime
 * @version 0.1
 * @date 2024-03-20
 */

#ifndef LF_QNX_SUPPORT_H
#define LF_QNX_SUPPORT_H

#include "lf_platform_util.h"
#include "tag.h"

// QNX-specific includes
#include <sys/neutrino.h>
#include <pthread.h>


// Defines for formatting time in printf for QNX
#define PRINTF_TIME "%lld"
#define PRINTF_MICROSTEP "%d"
#define PRINTF_TAG "(" PRINTF_TIME ", " PRINTF_MICROSTEP ")"

// QNX-specific mutex implementation
typedef struct {
    pthread_mutex_t mutex;
} lf_mutex_t;

// QNX-specific thread implementation
typedef struct {
    pthread_t thread;
    int id;
} lf_thread_t;

// QNX-specific condition variable implementation
typedef struct {
    pthread_cond_t cond;
    lf_mutex_t* mutex;
} lf_cond_t;

// QNX-specific clock implementation
typedef struct {
    uint64_t start_time;
    uint64_t resolution;
} lf_clock_t;

// Function declarations
int lf_mutex_init(lf_mutex_t* mutex);
int lf_mutex_lock(lf_mutex_t* mutex);
int lf_mutex_unlock(lf_mutex_t* mutex);
void lf_mutex_destroy(lf_mutex_t* mutex);

int lf_thread_create(lf_thread_t* thread, void* (*func)(void*), void* arg);
int lf_thread_join(lf_thread_t thread, void** thread_return);
int lf_thread_id(void);

int lf_cond_init(lf_cond_t* cond, lf_mutex_t* mutex);
int lf_cond_broadcast(lf_cond_t* cond);
int lf_cond_signal(lf_cond_t* cond);
int lf_cond_wait(lf_cond_t* cond);
int _lf_cond_timedwait(lf_cond_t* cond, instant_t wakeup_time);

void lf_clock_init(lf_clock_t* clock);
uint64_t lf_clock_get_time(lf_clock_t* clock);
uint64_t lf_clock_get_resolution(lf_clock_t* clock);

#endif // LF_QNX_SUPPORT_H 