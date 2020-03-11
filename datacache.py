from config import *
from cache_block import *
from cache_set import *


class DataCache:

    sets = []
    lru_for_cache_block = [0, 0]
    no_of_request = 0
    no_of_hit = 0

    def __init__(self):
        for i in range(CACHE_SETS):
            DataCache.sets.append(SetCache(i, CACHE_SIZE / CACHE_SETS))


    @classmethod
    def readcache(self, address):
        DataCache.no_of_request += 1
        address -= MEMORY_BASE_ADDRESS
        block_number = (address >> 4) % 2
        read_cycles = 0

        for i in range(CACHE_SETS):
            if DataCache._if_address_in_set(address, i):
                DataCache.no_of_hit += 1
                DataCache._set_lru(block_number, i)
                return HIT, DataCache.sets[i].cache_block[block_number].words[(address & 12) >> 2], ACCESS_TIME['DCACHE']

        set_no = DataCache.lru_for_cache_block[block_number]

        if DataCache.sets[set_no].cache_block[block_number].dirty:
            read_cycles += DataCache._write_back(set_no, block_number)

        DataCache._setup_block(address, set_no)
        read_cycles += (ACCESS_TIME['DCACHE'] + ACCESS_TIME['MEMORY']) * 2
        return MISS, DataCache.sets[set_no].cache_block[block_number].words[(address & 12) >> 2], read_cycles


    @classmethod
    def writecache(self, address, value, writable = True):
        DataCache.no_of_request += 1
        address -= MEMORY_BASE_ADDRESS
        block_number = (address >> 4) % 2
        write_cycles = 0

        for i in range(CACHE_SETS):
            if DataCache._if_address_in_set(address, i):
                DataCache.no_of_hit += 1
                DataCache._set_lru(block_number, i)
                DataCache._set_value(address, i, value, writable)
                return HIT, ACCESS_TIME['DCACHE']

        set_no = DataCache.lru_for_cache_block[block_number]

        if DataCache.sets[set_no].cache_block[block_number].dirty:
            write_cycles += DataCache._write_back(set_no, block_number)

        DataCache._setup_block(address, set_no)
        DataCache._set_value(address, set_no, value, writable)
        return MISS, write_cycles + (ACCESS_TIME['DCACHE'] + ACCESS_TIME['MEMORY']) * 2


    @classmethod
    def if_hit(self, address):
        address -= MEMORY_BASE_ADDRESS
        for i in range(CACHE_SETS):
            if DataCache._if_address_in_set(address, i):
                return True
        return False


    @classmethod
    def _if_address_in_set(self, address, set_no):
        tag = address >> 5
        block_number = (address >> 4) % 2
        return DataCache.sets[set_no].is_block_valid(block_number) and DataCache.sets[set_no].tag_for_block(block_number) == tag


    @classmethod
    def _write_back(self, set_no, block_number):
        tag = DataCache.sets[set_no].cache_block[block_number].tag
        base_address = MEMORY_BASE_ADDRESS + ((tag << 5) | (block_number << 4))
        for i in range(CACHE_BLOCK_SIZE):
            DATA[base_address + (i * WORD_SIZE)] = DataCache.sets[set_no].cache_block[block_number].words[i]
        return (ACCESS_TIME['DCACHE'] + ACCESS_TIME['MEMORY']) * 2


    @classmethod
    def _setup_block(self, address, set_no):
        block_number = (address >> 4) % 2
        DataCache.sets[set_no].cache_block[block_number].tag = address >> 5
        DataCache.sets[set_no].cache_block[block_number].valid = True
        DataCache._set_lru(block_number, set_no)
        DataCache._memory_read(address, set_no)


    @classmethod
    def _set_lru(self, block_number, set_no):
        DataCache.lru_for_cache_block[block_number] = 1 if set_no == 0 else 0


    @classmethod
    def _memory_read(self, address, set_no):
        block_number = (address >> 4) % 2
        base_address = MEMORY_BASE_ADDRESS + ((address >> 4) << 4)
        for i in range(CACHE_BLOCK_SIZE):
            DataCache.sets[set_no].cache_block[block_number].words[i] = DATA[base_address + (i * WORD_SIZE)]


    @classmethod
    def _set_value(self, address, set_no, value, writable):
        block_number = (address >> 4) % 2
        DataCache.sets[set_no].cache_block[block_number].dirty = True
        if writable:
            DCache.sets[set_no].cache_block[block_number_].words[(address & 12) >> 2] = value
