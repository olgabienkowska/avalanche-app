One of the things I enjoy the most is freeride skiing; but obviously, it comes with avalanche risk. 
When researching new spots, I check the usual things like routes and elevations (FATMAP (by Strava), you’ll be missed this winter 😿). 
But I also wanted to simplify assessing how common avy accidents are in the area.

Because of that, I created a very simple web app that reads the avalanche reports (originally XML files), saves the output into a Postgres database 
and then passes it over to Gemini model for analysis. The app highlights past avalanche accidents in a given location and provides some more insights. F
or now, it runs on dummy data since I’m waiting for approval from LAWIS to use real data, but fingers crossed for the future!

Obviously, it’s just a PoC, but I really enjoyed working on it—it was a great way to crosscheck my technical skills with my passion for the mountains.
