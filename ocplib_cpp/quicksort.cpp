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


/*
 * Quick Sort Implementation in C using OpenMP 
 */

#include<stdint.h>
#include<stdlib.h>
#include<ocplib.h>

// cmpFunc for QuickSort

int cmpFunc ( const void * pa, const void * pb )
{
  const uint64_t (*a)[4] = (const uint64_t(*)[4] )pa;
  const uint64_t (*b)[4] = (const uint64_t(*)[4] )pb;
  
  if ( (*a)[0] == (*b)[0] )
    if ( (*a)[1] == (*b)[1] )
      if ( (*a)[2] == (*b)[2] )
        return (*a)[3] - (*b)[3];
      else
        return (*a)[2] - (*b)[2];
    else
      return (*a)[1] - (*b)[1];
  else
    return (*a)[0] - (*b)[0];
}

// Naive Implementation of Quicksort

void quicksort ( uint64_t locs[][4], int locsSize )
{
  int i;
  qsort ( locs , locsSize, 4*sizeof(uint64_t), cmpFunc );
}

