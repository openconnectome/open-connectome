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
 * Filter Cutout Function 
 * Naive implementation 
 */

#include<stdio.h>
#include<stdint.h>
#include<stdbool.h>
#include<ocplib.h>

void filterCutout( uint32_t * cutout, int cutoutsize, uint32_t * filterlist, int listsize)
{
		int i,j;
		bool equal;

		for ( i=0; i<cutoutsize; i++)
		{
				equal = false;
				for ( j=0; j<listsize; j++)
				{
					// Checking if element in cutout exits in filterlist	
					if( cutout[i] == filterlist[j] )
					{
							equal = true;
							// Using break to exit because it exists in the list
							break;
					}
				}
				if( !equal )
						cutout[i] = 0;
		}
}
