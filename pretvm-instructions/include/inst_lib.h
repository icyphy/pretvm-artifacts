#ifndef SCHEDULER_STATIC_FUNCTION_H
#define SCHEDULER_STATIC_FUNCTION_H

#include "scheduler_instructions.h"

/**
 * @brief Function type with a void* argument. To make this type represent a
 * generic function, one can write a wrapper function around the target function
 * and use the first argument as a pointer to a struct of input arguments
 * and return values.
 */
typedef void (*function_generic_t)(void *);

#ifndef LF_PRINT_DEBUG
#define LF_PRINT_DEBUG(A, ...) {};
#endif

/**
 * @brief Wrapper function for peeking a priority queue.
 */
void push_pop_peek_pqueue(void *self);

void execute_inst_ADD(size_t worker_number, operand_t op1, operand_t op2,
                      operand_t op3, bool debug, size_t *pc,
                      reaction_t **returned_reaction, bool *exit_loop);
void execute_inst_ADDI(size_t worker_number, operand_t op1, operand_t op2,
                       operand_t op3, bool debug, size_t *pc,
                       reaction_t **returned_reaction, bool *exit_loop);
void execute_inst_BEQ(size_t worker_number, operand_t op1, operand_t op2,
                      operand_t op3, bool debug, size_t *pc,
                      reaction_t **returned_reaction, bool *exit_loop);
void execute_inst_BGE(size_t worker_number, operand_t op1, operand_t op2,
                      operand_t op3, bool debug, size_t *pc,
                      reaction_t **returned_reaction, bool *exit_loop);
void execute_inst_BLT(size_t worker_number, operand_t op1, operand_t op2,
                      operand_t op3, bool debug, size_t *pc,
                      reaction_t **returned_reaction, bool *exit_loop);
void execute_inst_BNE(size_t worker_number, operand_t op1, operand_t op2,
                      operand_t op3, bool debug, size_t *pc,
                      reaction_t **returned_reaction, bool *exit_loop);
void execute_inst_DU(size_t worker_number, operand_t op1, operand_t op2,
                     operand_t op3, bool debug, size_t *pc,
                     reaction_t **returned_reaction, bool *exit_loop);
void execute_inst_EXE(size_t worker_number, operand_t op1, operand_t op2,
                      operand_t op3, bool debug, size_t *pc,
                      reaction_t **returned_reaction, bool *exit_loop);
void execute_inst_WLT(size_t worker_number, operand_t op1, operand_t op2,
                      operand_t op3, bool debug, size_t *pc,
                      reaction_t **returned_reaction, bool *exit_loop);
void execute_inst_WU(size_t worker_number, operand_t op1, operand_t op2,
                     operand_t op3, bool debug, size_t *pc,
                     reaction_t **returned_reaction, bool *exit_loop);
void execute_inst_JAL(size_t worker_number, operand_t op1, operand_t op2,
                      operand_t op3, bool debug, size_t *pc,
                      reaction_t **returned_reaction, bool *exit_loop);
void execute_inst_JALR(size_t worker_number, operand_t op1, operand_t op2,
                       operand_t op3, bool debug, size_t *pc,
                       reaction_t **returned_reaction, bool *exit_loop);
void execute_inst_STP(size_t worker_number, operand_t op1, operand_t op2,
                      operand_t op3, bool debug, size_t *pc,
                      reaction_t **returned_reaction, bool *exit_loop);

#endif
