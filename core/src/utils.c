#include <dlfcn.h>
#include <unistd.h>
#include <stdlib.h>
#include "utils.h"

unsigned long long *ext_common_ticktime__ = NULL;
unsigned long tick__ = 0;

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

// void ext_setBufferPointers(IEC_BOOL *input_bool[BUFFER_SIZE][8], IEC_BOOL *output_bool[BUFFER_SIZE][8]) {
//     for (int i = 0; i < BUFFER_SIZE; i++) {
//         for (int j = 0; j < 8; j++) {
//             bool_input[i][j] = input_bool[i][j];
//             bool_output[i][j] = output_bool[i][j];
//         }
//     }
// }

void symbols_init(void){
        char *error = dlerror();
    #ifdef __APPLE__
        void *handle = dlopen("./libplc.dylib", RTLD_LAZY);
    #else
        void *handle = dlopen("./libplc.so", RTLD_LAZY);
    #endif
    if (!handle)
    {
        log_error("dlopen failed: %s\n", dlerror());
        exit(1);
    }

    // Clear any existing error
    dlerror();

    // Get pointer to external functions
    *(void **)(&ext_config_run__) = dlsym(handle, "config_run__");
    error = dlerror();
    if (error)
    {
        log_error("dlsym function error: %s\n", error);
        dlclose(handle);
        exit(1);
    }

    *(void **)(&ext_config_init__) = dlsym(handle, "config_init__");
    error = dlerror();
    if (error)
    {
        log_error("dlsym function error: %s\n", error);
        dlclose(handle);
        exit(1);
    }

    *(void **)(&ext_glueVars) = dlsym(handle, "glueVars");
    error = dlerror();
    if (error)
    {
        log_error("dlsym function error: %s\n", error);
        dlclose(handle);
        exit(1);
    }

    *(void **)(&ext_updateTime) = dlsym(handle, "updateTime");
    error = dlerror();
    if (error)
    {
        log_error("dlsym function error: %s\n", error);
        dlclose(handle);
        exit(1);
    }

    *(void **)(&ext_setBufferPointers) = dlsym(handle, "setBufferPointers");
    error = dlerror();
    if (error)
    {
        log_error("dlsym function error: %s\n", error);
        dlclose(handle);
        exit(1);
    }

    *(void **)(&ext_common_ticktime__) = dlsym(handle, "common_ticktime__");
    error = dlerror();
    if (error)
    {
        log_error("dlsym function error: %s\n", error);
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
}
