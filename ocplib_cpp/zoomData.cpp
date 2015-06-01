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
 * Zoom Data Functions
 * Naive implementation 
 */

#include<stdint.h>
#include<math.h>
#include<omp.h>
#include<ocplib.h>

void zoomOutData( uint32_t * olddata, uint32_t * newdata, int * dims, int factor )
{
		int i,j,k;

    int zdim = dims[0];
    int ydim = dims[1];
    int xdim = dims[2];
   
    int oldindex,newindex;
    int power = pow(2,factor);

		for ( i=0; i<zdim; i++ )
      for ( j=0; j<ydim; j++ )
        for ( k=0; k<xdim; k++ )
        {
          newindex = (i*xdim*ydim)+(j*xdim)+(k);
          oldindex = ( i*(xdim*power)*(ydim*power) ) + ( (j*power)*(xdim*power) ) + ( k*power );
          newdata[newindex] = olddata[oldindex];
        }
}


void zoomOutDataOMP( uint32_t * olddata, uint32_t * newdata, int * dims, int factor )
{
		int i,j,k;

    int zdim = dims[0];
    int ydim = dims[1];
    int xdim = dims[2];
   
    int oldindex,newindex;
    int power = pow(2,factor);

#pragma omp parallel num_threads(omp_get_max_threads())
    {
#pragma omp for private(i,j,k) schedule(dynamic)
      for ( i=0; i<zdim; i++ )
        for ( j=0; j<ydim; j++ )
          for ( k=0; k<xdim; k++ )
          {
            newindex = (i*xdim*ydim)+(j*xdim)+(k);
            oldindex = ( i*(xdim*power)*(ydim*power) ) + ( (j*power)*(xdim*power) ) + ( k*power );
            newdata[newindex] = olddata[oldindex];
          }
    }
}


void zoomInData( uint32_t * olddata, uint32_t * newdata, int * dims, int factor )
{
		int i,j,k;

    int zdim = dims[0];
    int ydim = dims[1];
    int xdim = dims[2];
   
    int oldindex,newindex;
    int power = pow(2,factor);

		for ( i=0; i<zdim; i++ )
      for ( j=0; j<ydim; j++ )
        for ( k=0; k<xdim; k++ )
        {
          newindex = (i*xdim*ydim)+(j*xdim)+(k);
          oldindex = ( i*(xdim/power)*(ydim/power) ) + ( (j/power)*(xdim/power) ) + ( k/power );
          newdata[newindex] = olddata[oldindex];
        }
}


void zoomInDataOMP( uint32_t * olddata, uint32_t * newdata, int * dims, int factor )
{
		int i,j,k;

    int zdim = dims[0];
    int ydim = dims[1];
    int xdim = dims[2];
   
    int oldindex, newindex;
    int power = pow(2,factor);

#pragma omp parallel num_threads(omp_get_max_threads())
    {
#pragma omp for private(i,j,k) schedule(dynamic)
      for ( i=0; i<zdim; i++ )
        for ( j=0; j<ydim; j++ )
          for ( k=0; k<xdim; k++ )
          {
            newindex = (i*xdim*ydim)+(j*xdim)+(k);
            oldindex = ( i*(xdim/power)*(ydim/power) ) + ( (j/power)*(xdim/power) ) + ( k/power );
            newdata[newindex] = olddata[oldindex];
          }
    }
}
