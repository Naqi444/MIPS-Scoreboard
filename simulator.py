from collections import deque
from implementable import *
from parser import *
from instcache import *
from datacache import *
from config import *
import operator
import sys


result = []


def cache_initialization():
    InstCache()
    DataCache()



def write_back_prioritize(new_queue, ex_queue):
    priority_map = {}
    count = MAX

    for i in range(len(ex_queue)):
        ex = ex_queue.pop()

        if ex._instruction.func_unit() == 'FP_DIV':
            if FP_DIV['PIPELINED']:
                priority_map[ex] = count + FP_DIV['CYCLES']
            else:
                priority_map[ex] = count + FP_DIV['CYCLES'] + MAX

        elif ex._instruction.func_unit() == 'FP_MUL':
            if FP_MUL['PIPELINED']:
                priority_map[ex] = count + FP_MUL['CYCLES']
            else:
                priority_map[ex] = count + FP_MUL['CYCLES'] + MAX

        elif ex._instruction.func_unit() == 'FP_ADD':
            if FP_ADD['PIPELINED']:
                priority_map[ex] = count + FP_ADD['CYCLES']
            else:
                priority_map[ex] = count + FP_ADD['CYCLES'] + MAX

        else:
            priority_map[ex] = count

        count -= 1

    sorted_m = sorted(priority_map.iteritems(), key=operator.itemgetter(1), reverse=True)
    for element in sorted_m:
        new_queue.appendleft(element[0])

    return new_queue



def rearrange_inst(old_queue):
    new_queue = deque([])

    for i in range(len(old_queue)):
        instruction = old_queue.pop()
        if instruction.current_stage.name == 'WB':
            new_queue.appendleft(instruction)
        else:
            old_queue.appendleft(instruction)

    ex_queue = deque([])
    for i in range(len(old_queue)):
        instruction = old_queue.pop()
        if instruction.current_stage.name == 'EX':
            ex_queue.appendleft(instruction)
        else:
            old_queue.appendleft(instruction)
    new_queue = write_back_prioritize(new_queue, ex_queue)

    for i in range(len(old_queue)):
        instruction = old_queue.pop()
        if instruction.current_stage.name == 'ID':
            new_queue.appendleft(instruction)
        else:
            old_queue.appendleft(instruction)

    for i in range(len(old_queue)):
        instruction = old_queue.pop()
        if instruction.current_stage.name == 'IF':
            new_queue.appendleft(instruction)
        else:
            old_queue.appendleft(instruction)

    return new_queue



def run_simulation():
    global result

    instruction_queue = deque([])
    clock_cycle = 1
    REGISTER['PC'] = 1
    instruction_queue.appendleft(Implementable(INSTRUCTIONS[0], clock_cycle))

    while len(instruction_queue) > 0:
        instruction_queue = rearrange_inst(instruction_queue)
        transfer_queue = deque([])
        while len(instruction_queue) > 0:
            instruction = instruction_queue.pop()
            if instruction.resume_implementation():
                transfer_queue.appendleft(instruction)
            else:
                result.append(instruction.result)

        instruction_queue = transfer_queue

        clock_cycle += 1

        if STAGE['IF'] == FREE and REGISTER['PC'] < len(INSTRUCTIONS):
            instruction_queue.appendleft(Implementable(INSTRUCTIONS[REGISTER['PC']], clock_cycle))
            REGISTER['PC'] += 1



def final_result(filename):
    res = sorted(result, key=lambda x: x.IF_cycle)
    res[len(res) - 1].ID_cycle = 0

    output = ''
    output += '-' * 94 + '\n'
    output += '\tInstruction\t\tFT\tID\tEX\tWB\tRAW\tWAR\tWAW\tStruct\n'
    output += '-' * 94 + '\n'

    for i in range(len(res)):
        found_label = False
        for label, address in LABEL.items():
            if res[i].instruction.address == address:
                found_label = True
                output += label + ':\t'
        if not found_label:
            output += '\t'
        output += str(res[i]) + '\n'

    output += '-' * 94 + '\n'
    output += '\nTotal number of requests for instruction cache: ' + str(InstCache.no_of_request)
    output += '\nNumber of instruction cache hits: ' + str(InstCache.no_of_hit)
    output += '\nTotal number of requests for data cache: ' + str(DataCache.no_of_request)
    output += '\nNumber of data cache hits: ' + str(DataCache.no_of_hit)

    file = open(filename, 'w')
    file.write(output)
    file.close()
    print output



if  __name__ == '__main__':
    if len(sys.argv) != 6:
        print('Usage: python simulator.py inst.txt data.txt reg.txt config.txt result.txt')
        exit()

    try:
        Parser.instructions_parser(sys.argv[1])
        Parser.data_parser(sys.argv[2])
        Parser.registers_parser(sys.argv[3])
        Parser.configuration_parser(sys.argv[4])
    except Exception as e:
        print('Parse Exception: ' + str(e))
        exit()

    cache_initialization()
    run_simulation()
    final_result(sys.argv[5])
