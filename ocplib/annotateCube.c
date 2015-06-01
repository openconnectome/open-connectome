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
 * Annotate Cube Function 
 * Naive implementation 
 */

#include<stdint.h>
#include<ocplib.h>

int annotateCube( uint32_t * data, int dataSize, int * dims, int annid, uint32_t * offset,  uint32_t locations[][3], int locationsSize, char conflictopt, uint32_t exceptions[][3] )
{
		int i,j,index;
    uint32_t xoffset = offset[0];
    uint32_t yoffset = offset[1];
    uint32_t zoffset = offset[2];

    int xdim = dims[0];
    int ydim = dims[1];
    int zdim = dims[2];

    int exceptionIndex = -1;

		for ( i=0; i<locationsSize; i++ )
		{

      index = (locations[i][2]-zoffset)*(ydim*zdim) + (locations[i][1]-yoffset)*(zdim) + (locations[i][0]-xoffset);

      // Label unlabeled voxels
      if ( data [ index ] == 0 )
      {
        data [ index ] = annid;
      }
      
      // Already labelled voxels are exceptions, unless they are the same value
      else if ( data [ index ] !=annid )
      {
        // 0 is for overwrite
        if ( conflictopt == 'O' )
        {
          data [ index ] = (uint32_t)annid;
        }
        // P preserves the existing content
        else if ( conflictopt == 'P' )
        {
          continue;
        }
        // E creates exceptions
        else if ( conflictopt == 'E' )
        {
          exceptionIndex += 1;
          exceptions [exceptionIndex][0] = locations[i][0]-xoffset;
          exceptions [exceptionIndex][1] = locations[i][1]-yoffset;
          exceptions [exceptionIndex][2] = locations[i][2]-zoffset;
        }
      }
      else
      {
        continue;
      }
      
		}
    return exceptionIndex;
}
