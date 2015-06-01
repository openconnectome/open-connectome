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
 * Locate Cube Function 
 * Naive implementation 
 */

#include<stdint.h>
#include<ocplib.h>

void locateCube( uint64_t locs[][4], int locsSize, uint32_t locations[][3], int locationsSize, int * dims )
{
		int i;

    int xdim = dims[0];
    int ydim = dims[1];
    int zdim = dims[2];

    uint64_t cubeno[3];
    
		for ( i=0; i<locationsSize; i++)
		{
      cubeno[0] = locations[i][0]/xdim;
      cubeno[1] = locations[i][1]/ydim;
      cubeno[2] = locations[i][2]/zdim;

      uint64_t cubekey = XYZMorton ( cubeno );

      locs[i][0] = cubekey;
      locs[i][1] = locations[i][0];
      locs[i][2] = locations[i][1];
      locs[i][3] = locations[i][2];
		}
    
}
