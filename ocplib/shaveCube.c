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
 * Shave Cube Function 
 * Naive implementation 
 */

#include<stdint.h>
#include<ocplib.h>

void shaveCube( uint32_t * data, int dataSize, int * dims, int annid, uint32_t * offset,  uint32_t locations[][3], int locationsSize, uint32_t exceptions[][3], int exceptionIndex, uint32_t zeroed[][3], int zeroedIndex )
{
		int i,j,index;
    uint32_t xoffset = offset[0];
    uint32_t yoffset = offset[1];
    uint32_t zoffset = offset[2];

    int xdim = dims[0];
    int ydim = dims[1];
    int zdim = dims[2];

    exceptionIndex = -1;
    zeroedIndex = -1;

		for ( i=0; i<locationsSize; i++ )
		{

      index = (locations[i][2]-zoffset)*(ydim*zdim) + (locations[i][1]-yoffset)*(zdim) + (locations[i][0]-xoffset);
      
      // if it's labeled then remove label
      if ( data [ index ] == annid )
      {
        data [ index ] = 0;
        //printf ( "Append zeroed" );
        zeroedIndex += 1;
        exceptions [zeroedIndex][0] = locations[i][0]-xoffset;
        exceptions [zeroedIndex][1] = locations[i][1]-yoffset;
        exceptions [zeroedIndex][2] = locations[i][2]-zoffset;
      }
      
      // Already labelled voxels may be in the exceptions list
      else if ( data [ index ] != 0 )
      {
        exceptionIndex += 1;
        exceptions [exceptionIndex][0] = locations[i][0]-xoffset;
        exceptions [exceptionIndex][1] = locations[i][1]-yoffset;
        exceptions [exceptionIndex][2] = locations[i][2]-zoffset;
      }
    }
}
