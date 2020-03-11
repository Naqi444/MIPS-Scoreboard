from config import *
from cache_block import *


class InstCache:

    cache_block = []
    no_of_request = 0
    no_of_hit = 0

    def __init__(self):
        for i in range(CACHE_SIZE):
            InstCache.cache_block.append(CacheBlock(i, CACHE_BLOCK_SIZE))


    @classmethod
    def readcache(self, address):
        InstCache.no_of_request += 1
        tag = address >> 6
        block_number = (address >> 4) % 4
        if InstCache.cache_block[block_number].valid == True and InstCache.cache_block[block_number].tag == tag:
            InstCache.no_of_hit += 1
            return HIT, ACCESS_TIME['ICACHE']
        else:
            InstCache.cache_block[block_number].tag = tag
            InstCache.cache_block[block_number].valid = True
            return MISS, (ACCESS_TIME['ICACHE'] + ACCESS_TIME['MEMORY']) * 2
