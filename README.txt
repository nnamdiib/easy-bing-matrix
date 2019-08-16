--------- Files you should provide -------------
1. CentroidsTotal.txt -> containing all your coordinate input and output.
						 Each line should be <id> <lat> <lon>
						 Example: 1  23.5667 24.567767

2. times.txt --> This file should list out all the times you want need data for.
				 Example: 8:00AM
				 		  6:00PM
				 		  10:00AM

3. keys.txt --> This file should contain each Bing API key on a new line.

--------- Files that will be generated automatically -------

4. output.txt --> This will contain the main program results.

5. state.txt --> This file will save program state and will allow it to continue from
				 where it stops due to any API limits. You're advised not to change any values
				 unless you are sure of what you're doing, as it can make you lose any progress.
				 The file has 4 values on different lines.
				 Line 1: The value for the 'i' counter variable in the main for loop when an API limit was hit
				 Line 2: The value for the 'j' counter variable in the main for loop when an API limit was hit
				 Line 3: The value for the index of the time string when an API limit was hit.
				 Line 4: The index of the API key to be used to resume program execution