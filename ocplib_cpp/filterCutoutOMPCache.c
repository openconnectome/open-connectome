/*
* Copyright 2014 Open Connectome Project (http://openconnecto.me)
* 
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
* 
*     http://www.apache.org/licenses/LICENSE-2.0
* 
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*/

#include<stdio.h>
#include<stdint.h>
#include<omp.h>
#include<stdbool.h>

/* Sample Alignment Sizes */
#define ALIGNMENT 4096


void sortDataFirst (uint32_t * cutoutarray, int cutoutsize,  uint32_t * filterlist, int listsize )
{

  for ( int i=0; i<listsize; i++)
  {
    printf("HELLO");
  }
}


void filterCutoutOMPCache( uint32_t * cutout, int cutoutsize, uint32_t * filterlist, int listsize)
{
		int i,j;
		bool equal;

      
    /* Memory Align the cutout data */
    posix_memalign ( (void**)&cutoutarray, ALIGNMENT, cutoutsize * sizeof(uint32_t) );
    memcpy ( cutoutarray, cutout, cutoutsize * sizeof(uint32_t) );

    /* Memory Align the filter list */
    /*
    posix_memalign ( (void**)&filterarray, ALIGNMENT, listsize * sizeof(uint32_t) );
    memcpy ( filterarray, filterlist, listsize * sizeof(uint32_t) );
    */
    

    for ( int filter_len = 16; filter_len<=listsize; filter_len*=2 )

		printf("MAX THREADS: %d",omp_get_max_threads());
#pragma omp parallel num_threads(omp_get_max_threads()) 
		{
#pragma omp for private(i,j,equal) schedule(dynamic)
				for ( i=0; i<cutoutsize; i++)
				{
						equal = false;
						for( j=0; j<listsize; j++)
						{
								if( cutout[i] == filterlist[j] )
								{
										equal = true;
										break;
								}
						}
						if( !equal || cutout[i] > filterlist[j] )
								cutout[i] = 0;
				}
		int ID = omp_get_thread_num();
		printf("THREAD ID: %d",ID);
		}
}
