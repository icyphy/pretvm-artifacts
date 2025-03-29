#ifdef PLATFORM_QNX
/**
 * @file lf_qnx_support.c
 * @brief Implementation of QNX-specific platform support for the Lingua Franca runtime
 * @version 0.1
 * @date 2024-03-20
 */

#include "platform/lf_qnx_support.h"
// #include "platform/lf_platform_util.h"
#include "low_level_platform.h"
#include <stdlib.h>
#include <string.h>
#include <sys/neutrino.h>
#include <sys/syspage.h>
#include <time.h>
#include <errno.h>
#include <stdio.h>
#include <unistd.h>

// Thread ID counter
static int thread_id_counter = 0;
static pthread_mutex_t thread_id_mutex = PTHREAD_MUTEX_INITIALIZER;

// Clock initialization
void _lf_initialize_clock() {
    struct timespec res;
    int return_value = clock_getres(CLOCK_MONOTONIC, &res);
    if (return_value < 0) {
        lf_print_error_and_exit("Could not obtain resolution for CLOCK_MONOTONIC");
    }
    lf_print("---- System clock resolution: %ld nsec", res.tv_nsec);
}

// Clock gettime implementation
int _lf_clock_gettime(instant_t* t) {
    if (t == NULL) {
        return -1;
    }
    struct timespec tp;
    if (clock_gettime(CLOCK_MONOTONIC, &tp) != 0) {
        return -1;
    }
    *t = ((instant_t)tp.tv_sec) * BILLION + tp.tv_nsec;
    return 0;
}

int lf_sleep(interval_t sleep_duration) {
  struct timespec tp;
  tp.tv_sec = sleep_duration / BILLION;
  tp.tv_nsec = sleep_duration % BILLION;
  return clock_nanosleep(CLOCK_MONOTONIC, 0, &tp, NULL);
}

// Interruptable sleep implementation
int _lf_interruptable_sleep_until_locked(environment_t* env, instant_t wakeup_time) {
  (void)env;
  interval_t sleep_duration = wakeup_time - lf_time_physical();

  if (sleep_duration <= 0) {
    return 0;
  } else {
    return lf_sleep(sleep_duration);
  }
}

int lf_mutex_init(lf_mutex_t* mutex) {
    return pthread_mutex_init(&mutex->mutex, NULL);
}

int lf_mutex_lock(lf_mutex_t* mutex) {
    return pthread_mutex_lock(&mutex->mutex);
}

int lf_mutex_unlock(lf_mutex_t* mutex) {
    return pthread_mutex_unlock(&mutex->mutex);
}

void lf_mutex_destroy(lf_mutex_t* mutex) {
    pthread_mutex_destroy(&mutex->mutex);
}

int lf_thread_create(lf_thread_t* thread, void* (*func)(void*), void* arg) {
    pthread_mutex_lock(&thread_id_mutex);
    thread->id = thread_id_counter++;
    pthread_mutex_unlock(&thread_id_mutex);
    
    return pthread_create(&thread->thread, NULL, func, arg);
}

int lf_thread_join(lf_thread_t thread, void** thread_return) {
    return pthread_join(thread.thread, thread_return);
}

// int lf_thread_id(void) {
//     // QNX doesn't have pthread_getthreadid_np, so we'll use our own counter
//     pthread_t current = pthread_self();
//     return (int)(uintptr_t)current;  // Use thread pointer as ID
// }

lf_thread_t lf_thread_self() {
    lf_thread_t self;
    self.thread = pthread_self();
    self.id = (int)(uintptr_t)self.thread;  // Use thread pointer as ID
    return self;
}

int lf_cond_init(lf_cond_t* cond, lf_mutex_t* mutex) {
    cond->mutex = mutex;
    return pthread_cond_init(&cond->cond, NULL);
}

int lf_cond_broadcast(lf_cond_t* cond) {
    return pthread_cond_broadcast(&cond->cond);
}

int lf_cond_signal(lf_cond_t* cond) {
    return pthread_cond_signal(&cond->cond);
}

int lf_cond_wait(lf_cond_t* cond) {
    return pthread_cond_wait(&cond->cond, &cond->mutex->mutex);
}

int _lf_cond_timedwait(lf_cond_t* cond, instant_t wakeup_time) {
    struct timespec ts;
    ts.tv_sec = wakeup_time / 1000000000;
    ts.tv_nsec = wakeup_time % 1000000000;
    return pthread_cond_timedwait(&cond->cond, &cond->mutex->mutex, &ts);
}

void lf_clock_init(lf_clock_t* clock) {
    struct timespec res;
    clock_getres(CLOCK_MONOTONIC, &res);
    clock->resolution = res.tv_nsec;
    clock->start_time = ClockCycles();
}

uint64_t lf_clock_get_time(lf_clock_t* clock) {
    uint64_t cycles = ClockCycles();
    uint64_t cycles_per_sec = SYSPAGE_ENTRY(qtime)->cycles_per_sec;
    return (cycles - clock->start_time) * clock->resolution / cycles_per_sec;
}

uint64_t lf_clock_get_resolution(lf_clock_t* clock) {
    return clock->resolution;
}

int lf_available_cores() {
    // Get the number of processors from the system page
    // int num_processors = SYSPAGE_ENTRY(system_private)->num_cpu;
    int num_processors = sysconf(_SC_NPROCESSORS_ONLN);
    return num_processors;
}

#endif // PLATFORM_QNX

