#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <dlfcn.h>
#include <time.h>
#ifdef __APPLE__
#include <mach/mach_time.h>
#endif
#include <signal.h>
#include <stdint.h>
#include <stdatomic.h>
#include <pthread.h>

atomic_long plc_heartbeat = 0;

extern void* watchdog_thread(void*);

//#include <sched.h>

//struct sched_param param;

//param.sched_priority = 20;
//if (sched_setscheduler(0, SCHED_FIFO, &param) != 0) {
//    perror("sched_setscheduler");
//}

#include "./lib/iec_types.h"
#include "log.h"

#define BUFFER_SIZE		1024

time_t start_time;
time_t end_time;

void (*ext_config_run__)(unsigned long tick);
void (*ext_config_init__)(void);
void (*ext_glueVars)(void);
void (*ext_updateTime)(void);
void (*ext_setBufferPointers)(IEC_BOOL *input_bool[BUFFER_SIZE][8], IEC_BOOL *output_bool[BUFFER_SIZE][8]);

//Internal buffers for I/O and memory.
//Booleans
IEC_BOOL *bool_input[BUFFER_SIZE][8];
IEC_BOOL *bool_output[BUFFER_SIZE][8];

//Bytes
IEC_BYTE *byte_input[BUFFER_SIZE];
IEC_BYTE *byte_output[BUFFER_SIZE];

//Analog I/O
IEC_UINT *int_input[BUFFER_SIZE];
IEC_UINT *int_output[BUFFER_SIZE];

//32bit I/O
IEC_UDINT *dint_input[BUFFER_SIZE];
IEC_UDINT *dint_output[BUFFER_SIZE];

//64bit I/O
IEC_ULINT *lint_input[BUFFER_SIZE];
IEC_ULINT *lint_output[BUFFER_SIZE];

//Memory
IEC_UINT *int_memory[BUFFER_SIZE];
IEC_UDINT *dint_memory[BUFFER_SIZE];
IEC_ULINT *lint_memory[BUFFER_SIZE];


//IEC_BOOL *(*ext_bool_output)[8];
unsigned long long *ext_common_ticktime__ = NULL;
unsigned long tick__ = 0;

volatile sig_atomic_t keep_running = 1;

void handle_sigint(int sig) {
    (void) sig;
    keep_running = 0;
}

void normalize_timespec(struct timespec *ts) {
    while (ts->tv_nsec >= 1e9) {
        ts->tv_nsec -= 1e9;
        ts->tv_sec++;
    }
}

void sleep_until(struct timespec *ts, long period_ns) {
    ts->tv_nsec += period_ns;
    normalize_timespec(ts);
    #ifdef __APPLE__
        struct timespec now;
        clock_gettime(CLOCK_MONOTONIC, &now);

        time_t sec = ts->tv_sec - now.tv_sec;
        long nsec = ts->tv_nsec - now.tv_nsec;
        if (nsec < 0) {
            nsec += 1000000000;
            sec -= 1;
        }
        struct timespec delay = { .tv_sec = sec, .tv_nsec = nsec };
        nanosleep(&delay, NULL);
    #else
        clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, ts, NULL);
    #endif
}


void timespec_diff(struct timespec *a, struct timespec *b, struct timespec *result) 
{
    // Calculate the difference in seconds
    result->tv_sec = a->tv_sec - b->tv_sec;

    // Calculate the difference in nanoseconds
    result->tv_nsec = a->tv_nsec - b->tv_nsec;

    // Handle borrowing if nanoseconds are negative
    if (result->tv_nsec < 0) 
    {
        // Borrow 1 second (1e9 nanoseconds)
        --result->tv_sec;
        result->tv_nsec += 1000000000L;
    }
}

int main(int argc, char* argv[])
{
    (void) argc;
    (void) argv;
    log_set_level(LOG_LEVEL_DEBUG);

    // Define the max/min/avg/total cycle and latency variables used in REAL-TIME computation(in nanoseconds)
    long cycle_avg, cycle_max, cycle_min, cycle_total;
    long latency_avg, latency_max, latency_min, latency_total;
    cycle_max = 0;
    cycle_min = LONG_MAX;
    cycle_total = 0;
    latency_max = 0;
    latency_min = LONG_MAX;
    latency_total = 0;

    // Define the start, end, cycle time and latency time variables
    struct timespec cycle_start, cycle_end, cycle_time;
    struct timespec timer_start, timer_end, sleep_latency;

    pthread_t wd_thread;
    pthread_create(&wd_thread, NULL, watchdog_thread, NULL);

    //gets the starting point for the clock
    log_info("Getting current time");
    clock_gettime(CLOCK_MONOTONIC, &timer_start);

    char *error = dlerror();
    #ifdef __APPLE__
        void *handle = dlopen("./libplc.dylib", RTLD_LAZY);
    #else
        void *handle = dlopen("./libplc.so", RTLD_LAZY);
    #endif
    if (!handle)
    {
        fprintf(stderr, "dlopen failed: %s\n", dlerror());
        exit(1);
    }

    // Clear any existing error
    dlerror();

    // Get pointer to external functions
    *(void **)(&ext_config_run__) = dlsym(handle, "config_run__");
    error = dlerror();
    if (error)
    {
        fprintf(stderr, "dlsym function error: %s\n", error);
        dlclose(handle);
        exit(1);
    }

    *(void **)(&ext_config_init__) = dlsym(handle, "config_init__");
    error = dlerror();
    if (error)
    {
        fprintf(stderr, "dlsym function error: %s\n", error);
        dlclose(handle);
        exit(1);
    }

    *(void **)(&ext_glueVars) = dlsym(handle, "glueVars");
    error = dlerror();
    if (error)
    {
        fprintf(stderr, "dlsym function error: %s\n", error);
        dlclose(handle);
        exit(1);
    }

    *(void **)(&ext_updateTime) = dlsym(handle, "updateTime");
    error = dlerror();
    if (error)
    {
        fprintf(stderr, "dlsym function error: %s\n", error);
        dlclose(handle);
        exit(1);
    }

    *(void **)(&ext_setBufferPointers) = dlsym(handle, "setBufferPointers");
    error = dlerror();
    if (error)
    {
        fprintf(stderr, "dlsym function error: %s\n", error);
        dlclose(handle);
        exit(1);
    }

    *(void **)(&ext_common_ticktime__) = dlsym(handle, "common_ticktime__");
    error = dlerror();
    if (error)
    {
        fprintf(stderr, "dlsym function error: %s\n", error);
        dlclose(handle);
        exit(1);
    }

    // Get pointer to variables in .so
    /*
    ext_bool_output = (IEC_BOOL *(*)[8])dlsym(handle, "bool_output");
    error = dlerror();
    if (error)
    {
        fprintf(stderr, "dlsym buffer error: %s\n", error);
        dlclose(handle);
        exit(1);
    }
    */

    // Send buffer pointers to .so
    ext_setBufferPointers(bool_input, bool_output);

    tzset();
    time(&start_time);

    // Init PLC
    ext_config_init__();
    ext_glueVars();

    // Run PLC loop
    while (keep_running)
    {
    	atomic_store(&plc_heartbeat, time(NULL));

	    // Get the start time for the running cycle
        clock_gettime(CLOCK_MONOTONIC, &cycle_start);

        ext_config_run__(tick__++);
        ext_updateTime();
    	// Get the end time for the running cycle
        clock_gettime(CLOCK_MONOTONIC, &cycle_end);

	    // Compute the time usage in one cycle and do max/min/total comparison/recording
        timespec_diff(&cycle_end, &cycle_start, &cycle_time);
        if (cycle_time.tv_nsec > cycle_max)
            cycle_max = cycle_time.tv_nsec;
        if (cycle_time.tv_nsec < cycle_min)
            cycle_min = cycle_time.tv_nsec;
        cycle_total = cycle_total + cycle_time.tv_nsec;

        if (bool_output[0][0])
        {
            log_debug("bool_output[0][0]: %d", *bool_output[0][0]);
        }
        else
        {
            log_debug("bool_output[0][0] is NULL");
        }

        // printf("%d\n", *ext_common_ticktime__);

        // usleep((int)*ext_common_ticktime__ % 1000);
        sleep_until(&timer_start, (unsigned long long)*ext_common_ticktime__);

        // Get the sleep end point which is also the start time/point of the next cycle
        clock_gettime(CLOCK_MONOTONIC, &timer_end);
        // Compute the time latency of the next cycle(caused by sleep) and do max/min/total comparison/recording
        timespec_diff(&timer_end, &timer_start, &sleep_latency);
        if (sleep_latency.tv_nsec > latency_max)
            latency_max = sleep_latency.tv_nsec;
        if (sleep_latency.tv_nsec < latency_min)
            latency_min = sleep_latency.tv_nsec;
        latency_total = latency_total + sleep_latency.tv_nsec;

        // Compute/print the max/min/avg cycle time and latency
        cycle_avg = (long)cycle_total / tick__;
        latency_avg = (long)latency_total / tick__;
        log_debug("maximum/minimum/average cycle time | %ld/%ld/%ld | in ms",
            cycle_max / 1000, cycle_min / 1000, cycle_avg / 1000);
        log_debug("maximum/minimum/average latency | %ld/%ld/%ld | in ms",
            latency_max / 1000,   latency_min / 1000, latency_avg / 1000);
    }
}
