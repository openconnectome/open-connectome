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
 * Merge Cube Function 
 * Naive implementation 
 */

#include<stdint.h>
#include<ocplib.h>

void mergeCube( uint32_t * data, int * dims, int newid, int oldid )
{
		int i,j,k,index;

    int zdim = dims[0];
    int ydim = dims[1];
    int xdim = dims[2];

    for ( k=0; k<zdim; k++ )
      for ( j=0; j<ydim; j++ )
        for ( i=0; i<xdim; i++ )
        {
          index = (k*xdim*ydim) + (j*xdim) + (i);
          if ( data [index] == oldid )
            data [index] = newid;
        }
}
