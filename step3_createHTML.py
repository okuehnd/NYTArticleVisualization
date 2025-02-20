import pandas as pd
from datetime import datetime, timedelta
from pyproj import Proj, transform
from pyproj import Transformer
import zipfile
import os

#Find the cleaned file we created in the cleaning step
for root, dirs, files in os.walk("."): 
    if "sentiment_nyt.csv" in files:
        data_set_path = os.path.join(root, "sentiment_nyt.csv")
        folder_path = root
        break 

articles = pd.read_csv(data_set_path)

#Not necessary, but remove abstract so that the dataset include large text
articles.drop('abstract',axis = 1, inplace = True)

#Convert dates in dataset to datetime
articles['pub_date'] = (pd.to_datetime(articles['pub_date'])).dt.year

#Change binary sentiment values to 'Positive'/'Negative'
articles['sentiment'] = articles['sentiment'].apply(lambda x: "Positive" if x == 1 else "Negative")

#This project does not support a database
#By the expectation of linearity, we assume that any random sampling
#of articles will give representative results when considering the 
#sentiment of a topic or section

#Choose a random sample, change n to change the size of the sample
articles = articles.sample(n = 600000, random_state = 42)

#assign datasource
data = {
   'web_url' : articles['web_url'],
   'headline' : articles['headline'],
   'section' : articles['section_name'],
   'keywords': articles['keywords'],
   'pub_date': articles['pub_date'],
   'sentiment': articles['sentiment']
}

#create dataframe
data = pd.DataFrame(data)

# Convert DataFrame to JSON
data_source = data.to_json(orient='records')

# Generate HTML with embedded JSON
d3_html_code = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>D3 Interactive Plot</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <!-- NYT Fonts -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.cdnfonts.com/css/chomsky" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Libre+Franklin:wght@300;400;500;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Cheltenham:wght@300;400;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');

        body {{
            font-family: 'Roboto';
            margin: 0;
            padding: 0;
            height: 100%;
        }}

        .tabcontent {{
        display: none;
        height: 100%;
        }}

        h1 {{
            font-family: 'Chomsky', serif;
            font-weight: 400;
            color: #000000;
            font-size: 3.5rem;
            margin-bottom: 1.5rem;
            text-align: center;
        }}

        h3 {{
            font-family: 'Roboto';
            font-weight: 400;
            color: #333;
        }}

        h4 {{
            font-family: 'Roboto';
            font-weight: 400;
            color: #333;
        }}

        .line {{ fill: none; stroke-width: 2px; }}
        .positive {{ stroke: #309231; }}
        .negative {{ stroke: #E2574A; }}
        .dot {{ stroke-width: 1px; fill-opacity: 0.6; }}
        .positive-dot {{ fill: #309231; }}
        .negative-dot {{ fill: #E2574A; }}

        .plot-container {{
            margin-bottom: 20px;
            background-color: rgba(236, 235, 235, 0.399);
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            border: 1px solid #e2e2e2;
        }}

        .controls-section {{
            background-color:  rgba(236, 235, 235, 0.399);
            padding: 20px;
            border: 1px solid #e2e2e2;
            border-radius: 10px;
            margin-bottom: 20px;
        }}

        .control-item {{
            margin-bottom: 1.5rem;
        }}

        .form-label {{
            font-family: 'Roboto', serif;
            font-weight: 500;
            color: #333;
            margin-bottom: 0.5rem;
        }}

        .sections-container {{
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid #e2e2e2;
            padding: 0.75rem;
            background-color: rgba(255, 255, 255, 0.98);
        }}

        .sections-container::-webkit-scrollbar {{
            width: 6px;
        }}

        .sections-container::-webkit-scrollbar-track {{
            background: #f8f8f8;
        }}

        .sections-container::-webkit-scrollbar-thumb {{
            background: #666;
        }}

        .sections-container::-webkit-scrollbar-thumb:hover {{
            background: #444;
        }}

        .card {{
            border-radius: 0;
            border: 1px solid #e2e2e2;
            background-color: rgba(255, 255, 255, 0.98);
        }}

        .card-header {{
            background-color: #f8f8f8;
            border-bottom: 1px solid #e2e2e2;
            font-family: 'Roboto', serif;
            font-weight: 500;
        }}

        .form-control, .form-range {{
            border-color: #e2e2e2;
            border-radius: 0;
        }}

        .form-control:focus {{
            border-color: #666;
            box-shadow: none;
        }}

        .form-check-input:checked {{
            background-color: #333;
            border-color: #333;
        }}

        /* Adjust the vertical spacing of the main container */
        .container-fluid {{
            padding-top: 2rem; /* Reduced top padding */
            padding-bottom: 2rem; /* Reduced bottom padding */
        }}

        /* Ensure consistent spacing between sections */
        .row {{
            margin-top: 0;
            margin-bottom: 10px; /* Reduced spacing between rows */
        }}

        .year-slider-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 20px;
            width: 850px; /* Slightly wider than plot to account for label */
            margin-left: auto;
            margin-right: auto;
            background-color: rgba(236, 235, 235, 0.399);
        }}

        .year-slider-wrapper {{
            width: 800px;
            display: flex;
            align-items: center;
        }}

        .year-slider-wrapper .form-range {{
            width: 750px;
            margin-right: 10px;
        }}

        /* Optional: Additional styling to ensure consistent red appearance */
        .year-slider-wrapper .form-range::-webkit-slider-thumb {{
            background-color: #E2574A;
            border-color: #E2574A;
        }}

        .year-slider-wrapper .form-range::-moz-range-thumb {{
            background-color: #E2574A;
            border-color: #E2574A;
        }}
        #yearSlider {{
            accent-color: #353535;
            }}

            #yearSlider::-webkit-slider-runnable-track {{
            background-color: #353535;
            }}

            #yearSlider::-moz-range-track {{
            background-color: #353535;
            }}

            #yearSlider::-ms-track {{
            background-color: #353535;
            }}

        #yearSliderFreq {{
            accent-color: #353535;
            }}

            #yearSliderFreq::-webkit-slider-runnable-track {{
            background-color: #353535;
            }}

            #yearSliderFreq::-moz-range-track {{
            background-color: #353535;
            }}

            #yearSliderFreq::-ms-track {{
            background-color: #353535;
            }}
              /* New Styles for Header and Date Box Alignment */
              .header-container {{
            display: flex;
            align-items: left;
            justify-content: left;
            margin-bottom: 0rem;
        }}

        @media (max-width: 1000px) {{
            .header-container {{
                flex-direction: column;
                align-items: flex-start;
            }}

            .header-container {{
                width: 100%;
                margin-bottom: 1rem;
            }}
        }}

        .date-box {{
            width: 250px;
            max-width: 800px;
            font-size: 14px; /* Optional: Adjust the font size */
            font-weight: 500;
        }}

        .date-box span {{
            float: left;
            margin-right: 5px;
        }}

        /* Tab links container styling */
        .tablinks-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px; /* Add spacing between buttons */
            margin-bottom: 0px;
        }}

        /* Tab links styling */
        .tablink {{
            border: none;
            outline: none;
            padding: 10px 20px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            color: #333;
            border-radius: 5px;
            background-color: #ffffff;
        }}

        .tablink:hover {{
            background-color: #ddd;
            color: #000;
        }}

        .tablink.active {{
            background-color: #555;
            color: white;
        }}

        /* Alternative method if the above doesn't work */
        hr.thick-line {{
            display: block !important;
            height: 5px !important;
            background: #000000 !important;
            border: 0 !important;
            margin: 10px 0 !important;
        }}

    </style>
</head>
<body>
    <div class="container-fluid py-4">
        <!-- New row for Date Box -->
        <div class="row mb-4">
            <div class="header-container">
                <div class="date-box">
                  <p>&#x1F50D;</p>
                </div>
                <div class="col-md-9">
                  <h6 class="text-center">
                    <span><b>U.S.</b></span>&nbsp;&nbsp;
                    <span>INTERNATIONAL</span>&nbsp;&nbsp;
                    <span>CANADA</span>&nbsp;&nbsp;
                    <span>ESPAÑOL</span>
                  </h6>
                </div>
              </div>
            <div class="header-container">
                    <div class="date-box">
                        <span><h6>Thursday, December 12, 2024</h6></span>
                        <br>
                        <span><h6>Today's Paper</h6></span>
                    </div>
                    <div class="col-md-9">
                    <h1 class="text-center">The New York Times</h1>
                    </div>
            </div>
            <div class="tablinks-container">
                <button class="tablink" onclick="openPage('Home', this, '')" id="defaultOpen">Sentiment</button>
                <button class="tablink" onclick="openPage('Frequency', this, '')">Frequency</button>
                <button class="tablink" onclick="openPage('About', this, '')">About</button>
            </div>
            <hr class="thick-line">
            <div style="position: relative; display: flex; justify-content: center;">
              <span>
                <h5 class="d-inline mb-4" style="color: #dd0404;"><b>LIVE</b></h5>
                <h5 class="d-inline mb-0" style="margin-left: 5px;">The Media's Mood Ring: 25 Years of News Decoded</h5>
              </span>
            </div>
            <hr style="color: #000; border-color: #000; border-width: 2px;">

        </div>

<div id="Home" class="tabcontent">
        <!-- Existing row for centered slider -->
        <div class="row">
            <div class="col-md-12">
                <div class="year-slider-container">
                    <div class="year-slider-wrapper">
                        <input type="range" class="form-range" id="yearSlider" min="2000" max="2025" value="2000" style="color: #000;">
                        <span id="yearLabel">2000</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-3">
                <div class="controls-section">
                    <div class="control-item">
                        <label class="form-label">Sections:</label>
                        <div class="sections-container">
                            <div id="sections" class="d-flex flex-column gap-2"></div>
                        </div>
                    </div>

                    <div class="control-item">
                        <label class="form-label">Sentiments:</label>
                        <div id="sentiments" class="d-flex flex-column gap-2">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="positive" value="Positive" checked>
                                <label class="form-check-label" for="positive">Positive</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="negative" value="Negative" checked>
                                <label class="form-check-label" for="negative">Negative</label>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="controls-section">
                    <div class="control-item">
                        <label class="form-label">Keyword Search:</label>
                        <input type="text" class="form-control" id="keywordInput">
                    </div>

                    <div class="card">
                        <div class="card-header">
                            Articles
                        </div>
                        <div id="displayBox" class="card-body" style="height: 400px; overflow-y: scroll;">
                            <div id="articleList"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Main Content Area -->
            <div class="col-md-9">
                <div id="plotContainer">
                    <!-- First Plot Area -->
                    <div class="plot-container">
                        <span style="color: #dd0404;">
                            <h5 class="text-left d-inline mb-4"><b>LIVE</b></h5>
                            <span style="color: #dd0404; font-size: 10px; margin-left: 5px;">&#9679;</span>
                            <h6 class="text-left d-inline mb-0" style="margin-left: 5px;">Just Now</h6>
                          </span>
                        <h5 class="text-left mb-4"><b>Sentiment across sections </b></h3>
                        <svg id="plot1" width="1000" height="400"></svg>
                    </div>

                    <!-- Second Plot Area -->
                    <div class="plot-container">
                        <span style="color: #dd0404;">
                            <h5 class="text-left d-inline mb-4"><b>LIVE</b></h5>
                            <h6 class="text-left d-inline mb-0" style="margin-left: 5px;">1m ago</h6>
                          </span>
                        <h5 class="text-left mb-4"><b>Sentiment across keywords</b></h3>
                        <svg id="plot2" width="1000" height="400"></svg>
                    </div>
                </div>
            </div>
        </div>
</div>

<div id="Frequency" class="tabcontent">
    <!-- Existing row for centered slider -->
    <div class="row">
        <div class="col-md-12">
            <div class="year-slider-container">
                <div class="year-slider-wrapper">
                    <input type="range" class="form-range" id="yearSliderFreq" min="2000" max="2025" value="2000" style="color: #000;">
                    <span id="yearLabelFreq">2000</span>
                </div>
            </div>
        </div>
    </div>

    <div class="row">
        <div class="col-md-3">
            <div class="controls-section">
                <div class="control-item">
                    <label class="form-label">Sections:</label>
                    <div class="sections-container">
                        <div id="sections-freq" class="d-flex flex-column gap-2"></div>
                    </div>
                </div>

                <div class="control-item">
                    <label class="form-label">Sentiments:</label>
                    <div id="sentimentsfreq" class="d-flex flex-column gap-2">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="positivefreq" value="Positive" checked>
                            <label class="form-check-label" for="positive">Positive</label>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="negativefreq" value="Negative" checked>
                            <label class="form-check-label" for="negative">Negative</label>
                        </div>
                    </div>
                </div>
            </div>

            <div class="controls-section">
                <div class="control-item">
                    <label class="form-label">Keyword Search:</label>
                    <input type="text" class="form-control" id="keywordInputfreq" placeholder="Enter a keyword">
                    <button id="addKeywordButton">Add</button>
                    <div id="keywordBox" style="margin-top: 10px; padding: 5px; border: 1px solid #ccc; background-color: #f9f9f9;">
                        <!-- Entered keywords will appear here -->
                    </div>
                    <p id="keywordWarning" style="color: red; display: none;">Maximum of 2 keywords allowed!</p>
                </div>

                <div class="card">
                    <div class="card-header">
                        Articles
                    </div>
                    <div id="displayBoxfreq" class="card-body" style="height: 400px; overflow-y: scroll;">
                        <div id="articleListFreq"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Content Area -->
        <div class="col-md-9">
              <div id="plotContainer" style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <!-- First Plot Area -->
                    <div class="plot-container" style="flex: 1; padding-right: 20px;">
                        <span style="color: #dd0404;">
                            <h5 class="text-left d-inline mb-4"><b>LIVE</b></h5>
                            <span style="color: #dd0404; font-size: 10px; margin-left: 5px;">&#9679;</span>
                            <h6 class="text-left d-inline mb-0" style="margin-left: 5px;">Just Now</h6>
                        </span>
                        <h5 class="text-left mb-4"><b>Frequency across sections </b></h5>
                        <svg id="catPlot" width="1000" height="400"></svg>
                    </div>

                    <!-- Legend Area -->
                    <div id="catLegend" style="
                        display: grid;
                        grid-template-rows: repeat(auto-fill, 20px); /* Fixed height per item */
                        grid-auto-flow: column; /* Fills column-first */
                        height: 400px; /* Match the plot height */
                        gap: 5px; /* Consistent spacing between items */
                        overflow: hidden; /* Prevent overflow outside the legend box */
                        width: 300px; /* Set width for the legend box */
                        margin-left: 20px;
                        border: 1px solid #ccc; /* Optional: Debugging border */
                    "></div>
                </div>


                <!-- Second Plot Area -->
                <div id="plotContainer" style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <!-- Plot Area -->
                    <div class="plot-container" style="flex: 1; padding-right: 20px;">
                        <span style="color: #dd0404;">
                            <h5 class="text-left d-inline mb-4"><b>LIVE</b></h5>
                            <h6 class="text-left d-inline mb-0" style="margin-left: 5px;">1m ago</h6>
                        </span>
                        <h5 class="text-left mb-4"><b>Frequency across keywords</b></h5>
                        <svg id="plot" width="1000" height="400"></svg>
                    </div>

                    <!-- Legend Area -->
                    <div id="legend" style="
                        display: grid;
                        grid-template-rows: repeat(auto-fill, 20px); /* Fixed height per item */
                        grid-auto-flow: column; /* Fills column-first */
                        height: 400px; /* Match the plot height */
                        gap: 5px; /* Consistent spacing between items */
                        overflow: hidden; /* Prevent overflow outside the legend box */
                        width: 300px; /* Set width for the legend box */
                        margin-left: 20px;
                        border: 1px solid #ccc; /* Optional: Debugging border */
                    "></div>
                </div>



            </div>
        </div>
    </div>
</div>


<div id="About" class="tabcontent">
     <!-- Main Content Area -->
     <div class="col-md-12">
        <div id="plotContainer">
            <!-- First Plot Area -->
            <div class="plot-container">
                <h4 class="text-center"><b>Contributors</b></h3>
                    <h6 class="text-center">Odette Kuehn (odk6560)</h6>
                    <h6 class="text-center">Rosemary Micky (rm6563) </h6>
                    <h6 class="text-center">Clely Fernandes (cvf9554)</h6>
            </div>
        </div>
    <div>

</div>
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>

    <script>
        function openPage(pageName, elmnt, color) {{
  // Hide all elements with class="tabcontent" by default */
  var i, tabcontent, tablinks;
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {{
    tabcontent[i].style.display = "none";
  }}

  // Remove the background color of all tablinks/buttons
  tablinks = document.getElementsByClassName("tablink");
  for (i = 0; i < tablinks.length; i++) {{
    tablinks[i].style.backgroundColor = "";
  }}

  // Show the specific tab content
  document.getElementById(pageName).style.display = "block";

  // Add the specific color to the button used to open the tab content
  elmnt.style.backgroundColor = color;
  elmnt.style.textDecoration = "underline"; // Add underline to the active tab
}}

// Get the element with id="defaultOpen" and click on it
document.getElementById("defaultOpen").click();
        </script>


    <script>
        let keywords = [];
        const colorScale = d3.scaleOrdinal(d3.schemeCategory10);
        function updateArticleDisplay(filteredData) {{
          updateLog("ARTICLE DISPLAY UPDATE CALLED")
          const keyword = d3.select("#keywordInput").property("value").toLowerCase();
          const selectedSections = Array.from(document.querySelectorAll("#sections input:checked")).map(d => d.value);
          const selectedSentiments = Array.from(document.querySelectorAll("#sentiments input:checked")).map(d => d.value);


          updateLog("ART1:");
          // Filter data based on selected criteria
          filteredData = data.filter(d =>
              (selectedSections.includes("All") || selectedSections.includes(d.section)) &&
              selectedSentiments.includes(d.sentiment) &&
              (d.keywords.includes(keyword))  // Filter by keyword
          );

          //updateLog(typeof filteredData[0].pub_date);

          updateLog("ART2:");


          // Group articles by year
          const articlesByYear = d3.group(filteredData, d => {{
              // Ensure pub_date is converted to a string
              const year = typeof d.pub_date === 'number'
                  ? d.pub_date.toString()
                  : String(d.pub_date);
              return year;
          }});


          // Convert Map to object for easier logging
          const articlesByYearObj = {{}};
          articlesByYear.forEach((value, key) => {{
              articlesByYearObj[key] = value;
          }});

          updateLog("ART3:");

          const articleListDiv = d3.select("#articleList");
          articleListDiv.html("");  // Clear previous entries

          updateLog("ART4:");

          // Iterate over each year group and create HTML structure
          Object.entries(articlesByYearObj).forEach(([year, articles]) => {{
              updateLog("IN ART YEAR1");
              const yearDiv = articleListDiv.append("div").attr("class", "yearGroup");
              updateLog("IN ART YEAR2");
              yearDiv.append("strong").text(year);  // Display the year
              updateLog("IN ART YEAR4");
              updateLog("YEAR GROUP " + JSON.stringify(articles));

              articles.forEach(article => {{
                  updateLog("IN ART YEAR5");
                  const articleDiv = yearDiv.append("div").attr("class", "article");
                  updateLog("IN ART YEAR6");
                  articleDiv
                      .html(`&#8226; ${{article.headline}}`)
                      .style("color", article.sentiment === "Positive" ? "green" : "red")
                      .style("cursor", "pointer")
                      .on("mouseover", function() {{
                          // Show the URL when hovering over the title
                          d3.select(this).append("span").text(" - " + article.web_url).style("color", "blue");
                          updateLog("MOUSE OVER");
                      }})
                      .on("mouseout", function() {{
                          // Remove the URL when not hovering
                          d3.select(this).select("span").remove();
                          updateLog("MOUSE OUT");
                      }})
                      .on("click", function() {{
                          // Open the URL when the title is clicked
                          window.open(article.web_url, "_blank");
                          updateLog("CLICK");
                      }});
                  updateLog("IN ART YEAR7");
              }});
          }});

          updateLog("ART5:");
          }}


        function updateLog(message) {{
            // const logMessages = document.getElementById("log_messages");
            // logMessages.innerHTML += message + "<br>";
            // logMessages.scrollTop = logMessages.scrollHeight;  // Scroll to bottom
        }}

        updateLog("Initial Log");

        // Sample data: Replace with your datasets
        const data = {data_source};


        updateLog("HERE1");
        const firstRow = data[0];  // Get the first row

        // Set up plot dimensions
        const svg1 = d3.select("#plot1");
        const svg2 = d3.select("#plot2");
        let margin = {{ top: 20, right: 30, bottom: 30, left: 40 }};
        let width = 1000 - margin.left - margin.right;
        let height = 320 - margin.top - margin.bottom;
        const plotArea1 = svg1.append("g").attr("transform", `translate(${{margin.left}},${{margin.top}})`);
        const plotArea2 = svg2.append("g").attr("transform", `translate(${{margin.left}},${{margin.top}})`);
        plotArea1.append("text")
            .attr("transform", `translate(${{width / 2}}, ${{height + margin.bottom - 10}})`)  // Position the x-axis label
            .style("text-anchor", "middle")
            .text("Year");

        plotArea1.append("text")
            .attr("transform", `translate(-100, ${{height / 2}}) rotate(-90)`)  // Position the y-axis label vertically
            .style("text-anchor", "middle")
            .text("Number of Articles");

        plotArea2.append("text")
            .attr("transform", `translate(${{width / 2}}, ${{height + margin.bottom - 10}})`)  // Position the x-axis label
            .style("text-anchor", "middle")
            .text("Year");

        plotArea2.append("text")
            .attr("transform", `translate(-100, ${{height / 2}}) rotate(-90)`)  // Position the y-axis label vertically
            .style("text-anchor", "middle")
            .text("Number of Articles");


        function addLegend(svg){{
          // Create a legend
          const legendWidth = 200;
          const legendHeight = 40;
          const legendSpacing = 20;  // Space between each item in the legend

          // Add a group for the legend
          const legend = svg.append("g")
              .attr("transform", `translate(${{width - margin.right}}, 20)`);  // Position the legend

          // Add a box for the positive sentiment
          legend.append("rect")
              .attr("x", 0)
              .attr("y", 0)
              .attr("width", 20)
              .attr("height", 20)
              .attr("fill", "green");  // Positive sentiment color

          // Add text for positive sentiment
          legend.append("text")
              .attr("x", 25)
              .attr("y", 15)
              .style("font-size", "12px")
              .text("Positive");

          // Add a box for the negative sentiment
          legend.append("rect")
              .attr("x", 0)
              .attr("y", legendSpacing)  // Add some space between the positive and negative boxes
              .attr("width", 20)
              .attr("height", 20)
              .attr("fill", "red");  // Negative sentiment color

          // Add text for negative sentiment
          legend.append("text")
              .attr("x", 25)
              .attr("y", legendSpacing + 15)
              .style("font-size", "12px")
              .text("Negative");


        }}

        addLegend(svg1);
        addLegend(svg2);

        // Render the plot
        function updatePlots() {{
          updateLog("HERE67");
            const year = +d3.select("#yearSlider").property("value");
            const selectedSections = Array.from(document.querySelectorAll("#sections input:checked")).map(d => d.value);
            const selectedSentiments = Array.from(document.querySelectorAll("#sentiments input:checked")).map(d => d.value);
            const keyword = d3.select("#keywordInput").property("value").toLowerCase();


            // Filter data based on selected criteria
            // Filter data for first plot (ignoring keywords)
            const filteredData1 = data.filter(d =>
                d.pub_date <= year &&
                (selectedSections.includes("All") || selectedSections.includes(d.section)) &&
                selectedSentiments.includes(d.sentiment)
            );

            // Filter data for second plot (including keywords)
            const filteredData2 = data.filter(d =>
                d.pub_date <= year &&
                (selectedSections.includes("All") || selectedSections.includes(d.section)) &&
                selectedSentiments.includes(d.sentiment) &&
                (d.keywords.includes(keyword))
            );
            updateLog("HERE68");
             // Update first plot
            updateSinglePlot(plotArea1, filteredData1, "");

            if (keyword){{
               // Update second plot
              updateSinglePlot(plotArea2, filteredData2, "");
              // Update article display
              updateArticleDisplay(filteredData2);
            }}
        }}

        updateLog("HERE7");

        function updateSinglePlot(plotArea, filteredData, title) {{
            const year = +d3.select("#yearSlider").property("value");
            const selectedSections = Array.from(document.querySelectorAll("#sections input:checked")).map(d => d.value);
            const selectedSentiments = Array.from(document.querySelectorAll("#sentiments input:checked")).map(d => d.value);
            const keyword = d3.select("#keywordInput").property("value").toLowerCase();
            // Clear existing plot
            plotArea.selectAll("*").remove();


            // Aggregate data for display
            const yearCountsPos = {{}};
            const yearCountsNeg = {{}};
            const years = Array.from({{ length: 2024 - 2000 + 1 }}, (_, i) => 2000 + i);

            years.forEach(y => {{
              if(y <= year){{
                yearCountsPos[y] = 0;
                yearCountsNeg[y] = 0;
              }}
            }});

            updateLog("HERE8");

            filteredData.forEach(d => {{

                if (d.sentiment === "Positive") {{
                    yearCountsPos[d.pub_date] = (yearCountsPos[d.pub_date] || 0) + 1;
                }} else if (d.sentiment === "Negative") {{
                    yearCountsNeg[d.pub_date] = (yearCountsNeg[d.pub_date] || 0) + 1;
                }}
            }});


            updateLog("HERE9");

            const years_pos = Object.keys(yearCountsPos).map(Number);
            const pos_frequency = Object.values(yearCountsPos);
            const years_neg = Object.keys(yearCountsNeg).map(Number);
            const neg_frequency = Object.values(yearCountsNeg);


            const maxPosFrequency = Math.max(...pos_frequency); // ...
            const maxNegFrequency = Math.max(...neg_frequency);
            const maxFrequency = Math.max(maxPosFrequency, maxNegFrequency);
            paddedMaxFreq = maxFrequency + 100;

            xScale = d3.scaleLinear()
                .domain([2000, year])
                .range([0, width]);

            yScale = d3.scaleLinear()
                .domain([0, paddedMaxFreq])
                .range([height, 0]);

            updateLog("YDOMAIN : "+yScale.domain());

            updateLog("HERE10");

            // Bind and update lines and dots
            const positiveData = years_pos.map((year, i) => ({{ year, frequency: pos_frequency[i] }}));
            const negativeData = years_neg.map((year, i) => ({{ year, frequency: neg_frequency[i] }}));

            updateLog("HERE11");

           // Add gridlines for x-axis
            plotArea.append("g")
                .attr("class", "grid")
                .attr("transform", `translate(0,${{height}})`)
                .call(d3.axisBottom(xScale)
                    .ticks(xScale.domain()[1] - xScale.domain()[0])
                    .tickSize(-height)
                    .tickFormat(""))
                .selectAll(".tick line")
                .attr("stroke", "gray")
                .attr("stroke-opacity", 0.6)
                .attr("shape-rendering", "crispEdges");

            // Add gridlines for y-axis
            plotArea.append("g")
                .attr("class", "grid")
                .call(d3.axisLeft(yScale)
                    .ticks(5)
                    .tickSize(-width)
                    .tickFormat(""))
                .selectAll(".tick line")
                .attr("stroke", "gray")
                .attr("stroke-opacity", 0.6)
                .attr("shape-rendering", "crispEdges");

            // Add axes with transitions
            plotArea.append("g")
                .attr("class", "x-axis")
                .attr("transform", `translate(0,${{height}})`)
                .transition()
                .duration(500)
                .call(d3.axisBottom(xScale)
                    .ticks(xScale.domain()[1] - xScale.domain()[0])
                    .tickSize(-height)
                    .tickFormat(d3.format("d")));

            const tickCount = (paddedMaxFreq / 100) % 10 + 10;
            plotArea.append("g")
                .attr("class", "y-axis")
                .transition()
                .duration(500)
                .call(d3.axisLeft(yScale).ticks(tickCount));

            plotArea.append("text")
            .attr("transform", `translate(${{width / 2}}, ${{height + margin.bottom - 10}})`)  // Position the x-axis label
            .style("text-anchor", "middle")
            .text("Year");

        plotArea.append("text")
            .attr("transform", `translate(-20, ${{height / 2}}) rotate(-90)`)  // Position the y-axis label vertically
            .style("text-anchor", "middle")
            .text("Number of Articles");

            // Create line generator
            const lineGenerator = d3.line()
                .x(d => xScale(d.year))
                .y(d => yScale(d.frequency));

            // Draw positive line with transition
            plotArea.selectAll(".line.positive")
                .data([positiveData])
                .join("path")
                .attr("class", "line positive")
                .transition()
                .duration(500)
                .attr("d", lineGenerator);

            // Draw negative line with transition
            plotArea.selectAll(".line.negative")
                .data([negativeData])
                .join("path")
                .attr("class", "line negative")
                .transition()
                .duration(500)
                .attr("d", lineGenerator);

            // Add title
            plotArea.append("text")
                .attr("x", width / 2)
                .attr("y", -5)
                .style("text-anchor", "middle")
                .text(title);

        }}


        // Initialize UI components
        const uniqueSections = Array.from(new Set(data.map(d => d.section)));
       // Initialize UI components
      const sectionsContainer = d3.select("#sections");

      // Add "All" checkbox first
      sectionsContainer.append("label")
          .html('<input type="checkbox" id="allSectionsCheckbox" value="All"> All');

      // Add section checkboxes
      sectionsContainer.selectAll(".section-label")
          .data(uniqueSections)
          .enter()
          .append("label")
          .attr("class", "section-label")
          .html(d => `<input type="checkbox" class="section-checkbox" value="${{d}}"> ${{d}}`);


      // Event listener
      document.getElementById('allSectionsCheckbox').addEventListener('change', function() {{
          updateLog("ALL SECTION CHANGE");
          const isChecked = this.checked;
          updateLog("CHANGE TO : " + isChecked);

          // Get all section checkboxes
          const sectionCheckboxes = document.querySelectorAll('.section-checkbox');

          // Enable or disable other checkboxes based on "All" selection
          if(isChecked){{
              sectionCheckboxes.forEach(checkbox => {{
                  checkbox.checked = false;
                  checkbox.disabled = true;
              }});
          }} else {{
              sectionCheckboxes.forEach(checkbox => {{
                  checkbox.disabled = false;
              }});
          }}

          // Trigger plot update
          updatePlots();
      }});

        //d3.selectAll(".section-checkbox").on("change", function () {{
          //const allChecked = d3.selectAll(".section-checkbox").nodes().every(node => node.checked);

          // Uncheck "All" if not all sections are selected
          //d3.select("#allSections").property("checked", allChecked === true);

          // Trigger plot update
         // updatePlots();
      //}});

        updateLog("HERE13");
        updateLog("Unique sections: " + uniqueSections.join(", "));
        // Attach event listeners
        d3.select("#yearSlider").on("input", function () {{
            d3.select("#yearLabel").text(this.value);
            updatePlots();
        }});

        updateLog("HERE14");
        d3.selectAll("#sections input, #sentiments input").on("change", updatePlots);
        d3.select("#keywordInput").on("keydown", function(event) {{
            if (event.key === "Enter") {{ // Check if the key pressed is Enter
                updatePlots();
            }}
        }});

        updateLog("HERE15");

        // Initial plot render
        updatePlots();









        /// --------------------------- ////

        const svg = d3.select("#plot");
        const svgCat = d3.select("#catPlot");
        margin = {{ top: 20, right: 30, bottom: 30, left: 40 }};
        width = svg.attr("width") - margin.left - margin.right;
        height = svg.attr("height") - margin.top - margin.bottom;
        plotArea = svg.append("g").attr("transform", `translate(${{margin.left}},${{margin.top}})`);
        catPlotArea = svgCat.append("g").attr("transform", `translate(${{margin.left}},${{margin.top}})`);


                // Create a legend
        const legendWidth = 200;
        const legendHeight = 40;
        const legendSpacing = 20;  // Space between each item in the legend

        // Add a group for the legend
    //    const legend = svg.append("g")
      //      .attr("id", "legend")
        //    .attr("transform", `translate(${{width - margin.right}}, 20)`);  // Position the legend

        //const catLegend = svgCat.append("g")
          //  .attr("id", "catLegend")
            //.attr("transform", `translate(${{width - margin.right}}, 20)`);  // Position the legend


        svg.append("text")
          .attr("x", width / 2)  // Center the title horizontally
          .attr("y", margin.top - 10)  // Position the title above the plot
          .style("text-anchor", "middle")  // Center the text
          .style("font-size", "16px")  // Set the font size
          .style("font-weight", "bold")  // Make the title bold

        svgCat.append("text")
          .attr("x", width / 2)  // Center the title horizontally
          .attr("y", margin.top - 10)  // Position the title above the plot
          .style("text-anchor", "middle")  // Center the text
          .style("font-size", "16px")  // Set the font size
          .style("font-weight", "bold")  // Make the title bold

        paddedMaxFreq = 50;

        xScale = d3.scaleLinear().domain([2000, 2023]).range([0, width]);  // Ensure correct domain and range
        yScale = d3.scaleLinear().domain([0, paddedMaxFreq]).range([height, 0]);

        xScaleCat = d3.scaleLinear().domain([2000, 2023]).range([0, width]);  // Ensure correct domain and range
        yScaleCat = d3.scaleLinear().domain([0, paddedMaxFreq]).range([height, 0]);

//////////////////ORIGINAL PLOT START///////////////////////////////////////////////////////////////////////
        plotArea.append("g")
            .attr("class", "grid")
            .attr("transform", `translate(0,${{height}})`) // Position at the bottom of the plot area
            .call(d3.axisBottom(xScale)
                .ticks(xScale.domain()[1] - xScale.domain()[0] + 1) // Adjust for 1-unit spacing
                .tickSize(-height) // Length of the grid lines
                .tickFormat("")) // Hide tick labels
            .selectAll(".tick line")
            .attr("stroke", "gray") // Color of the gridlines
            .attr("stroke-opacity", 0.6) // Set opacity to 0.6
            .attr("shape-rendering", "crispEdges"); // For sharp grid lines

        // Add gridlines for y-axis
        plotArea.append("g")
            .attr("class", "grid")
            .call(d3.axisLeft(yScale)
                .ticks(5) // Adjust the number of ticks for y-axis
                .tickSize(-width) // Length of the grid lines
                .tickFormat("")) // Hide tick labels
            .selectAll(".tick line")
            .attr("stroke", "gray") // Color of the gridlines
            .attr("stroke-opacity", 0.6) // Set opacity to 0.6
            .attr("shape-rendering", "crispEdges"); // For sharp grid lines

        // Add the x-axis ticks (after gridlines to keep them on top)
        plotArea.append("g")
          .attr("class", "x-axis")
          .attr("transform", `translate(0, ${{height}})`)
          .call(d3.axisBottom(xScale));

        plotArea.append("g")
          .attr("class", "y-axis")
          .call(d3.axisLeft(yScale));

        plotArea.append("text")
            .attr("transform", `translate(${{width / 2}}, ${{height + margin.bottom - 10}})`)  // Position the x-axis label
            .style("text-anchor", "middle")
            .text("Year");

        plotArea.append("text")
            .attr("transform", `translate(-20, ${{height / 2}}) rotate(-90)`)  // Position the y-axis label vertically
            .style("text-anchor", "middle")
            .text("Number of Articles");

        const lineGenerator = d3.line()
            .x(d => {{
                const scaledX = xScale(d.year);
                return scaledX +40;  //I Had to adjust this scalars until it looked fine but it worked so im leaving it
            }})
            .y(d => {{
                const scaledY = yScale(d.frequency);
                return scaledY + 20;
            }});
////////////////ORIGINAL PLOT END////////////////////////////////////////////////////////////////////////

//////////////////CAT PLOT START///////////////////////////////////////////////////////////////////////
        catPlotArea.append("g")
            .attr("class", "grid")
            .attr("transform", `translate(0,${{height}})`) // Position at the bottom of the plot area
            .call(d3.axisBottom(xScaleCat)
                .ticks(xScale.domain()[1] - xScale.domain()[0] + 1) // Adjust for 1-unit spacing
                .tickSize(-height) // Length of the grid lines
                .tickFormat("")) // Hide tick labels
            .selectAll(".tick line")
            .attr("stroke", "gray") // Color of the gridlines
            .attr("stroke-opacity", 0.6) // Set opacity to 0.6
            .attr("shape-rendering", "crispEdges"); // For sharp grid lines

        // Add gridlines for y-axis
        catPlotArea.append("g")
            .attr("class", "grid")
            .call(d3.axisLeft(yScaleCat)
                .ticks(5) // Adjust the number of ticks for y-axis
                .tickSize(-width) // Length of the grid lines
                .tickFormat("")) // Hide tick labels
            .selectAll(".tick line")
            .attr("stroke", "gray") // Color of the gridlines
            .attr("stroke-opacity", 0.6) // Set opacity to 0.6
            .attr("shape-rendering", "crispEdges"); // For sharp grid lines

        // Add the x-axis ticks (after gridlines to keep them on top)
        catPlotArea.append("g")
          .attr("class", "x-axis")
          .attr("transform", `translate(0, ${{height}})`)
          .call(d3.axisBottom(xScaleCat));

        catPlotArea.append("g")
          .attr("class", "y-axis")
          .call(d3.axisLeft(yScaleCat));

        catPlotArea.append("text")
            .attr("transform", `translate(${{width / 2}}, ${{height + margin.bottom - 10}})`)  // Position the x-axis label
            .style("text-anchor", "middle")
            .text("Year");

        catPlotArea.append("text")
            .attr("transform", `translate(-20, ${{height / 2}}) rotate(-90)`)  // Position the y-axis label vertically
            .style("text-anchor", "middle")
            .text("Number of Articles");

        const lineGeneratorCat = d3.line()
            .x(d => {{
                const scaledX = xScaleCat(d.year);
                return scaledX +40;  //I Had to adjust this scalars until it looked fine but it worked so im leaving it
            }})
            .y(d => {{
                const scaledY = yScaleCat(d.frequency);
                return scaledY + 20;
            }});
////////////////CAT PLOT END////////////////////////////////////////////////////////////////////////

        let lineCount = 0;
        let lineCountCat =0;

        function updateKeywordBox() {{
          const keywordBox = d3.select("#keywordBox");
          keywordBox.html(""); // Clear existing content
          keywords.forEach((keyword, index) => {{
              keywordBox
                  .append("span")
                  .style("display", "inline-block")
                  .style("margin", "2px")
                  .style("padding", "5px 10px")
                  .style("background-color", "#e0e0e0")
                  .style("border-radius", "5px")
                  .style("font-size", "14px")
                  .style("cursor", "default")
                  .html(`${{keyword}} <button data-index="${{index}}" style="margin-left: 5px; background-color: red; color: white; border: none; border-radius: 50%; width: 20px; height: 20px; cursor: pointer;">&times;</button>`);
          }});

          // Add event listeners to remove buttons
          d3.selectAll("#keywordBox button").on("click", function () {{
              const index = +this.getAttribute("data-index");
              keywords.splice(index, 1); // Remove keyword by index
              updateKeywordBox(); // Re-render keyword box
              updatePlot(); // Update plot
          }});
      }}

      function addCatLine(s,filteredData, year,selectedSentiments){{ //pass in section
         // keywordData
            const sectionData = filteredData.filter(d =>
                d.pub_date <= year &&
                (s == d.section) &&
                selectedSentiments.includes(d.sentiment)
            );

            // Aggregate data for display
            const yearCounts = {{}};
            const years = Array.from({{ length: 2024 - 2000 + 1 }}, (_, i) => 2000 + i);

            years.forEach(y => {{
              if(y <= year){{
                yearCounts[y] = 0;
              }}
            }});

            sectionData.forEach(d => {{
                yearCounts[d.pub_date] = (yearCounts[d.pub_date] || 0) + 1;
            }});

            const sectionPlot = {{
              year: Object.keys(yearCounts).map(key => parseInt(key)),
              frequency: Object.values(yearCounts)
            }};

            const lineData = sectionPlot.year.map((year, index) => ({{
                year: year,
                frequency: sectionPlot.frequency[index]
            }}));

            const scaledData = lineData.map(d => ({{
                year: xScaleCat(d.year),          // Scale the year (x-axis)
                frequency: yScaleCat(d.frequency) // Scale the frequency (y-axis)
            }}));
            const line = svgCat.append('path')
                .data([lineData])
                .attr('class', 'cat-line')
                .attr('d', lineGeneratorCat)
                .attr('stroke', colorScale(lineCountCat))
                .attr('stroke-width', 2)
                .attr('fill', 'none')

          updateLegendCat(s,lineCountCat);

            lineCountCat++;
      }}


      function addKeywordLine(keyword,filteredData, year, selectedSections,selectedSentiments){{
         // keywordData
            const keywordData = filteredData.filter(d =>
                d.pub_date <= year &&
                (selectedSections.includes("All")||selectedSections.includes(d.section)) &&
                selectedSentiments.includes(d.sentiment) &&
                (!keyword || d.keywords.includes(keyword))
            );

            // Aggregate data for display
            const yearCounts = {{}};
            const years = Array.from({{ length: 2024 - 2000 + 1 }}, (_, i) => 2000 + i);

            years.forEach(y => {{
              if(y <= year){{
                yearCounts[y] = 0;
              }}
            }});

            keywordData.forEach(d => {{
                yearCounts[d.pub_date] = (yearCounts[d.pub_date] || 0) + 1;
            }});

            const keywordPlot = {{
              year: Object.keys(yearCounts).map(key => parseInt(key)),
              frequency: Object.values(yearCounts)
            }};

            const lineData = keywordPlot.year.map((year, index) => ({{
                year: year,
                frequency: keywordPlot.frequency[index]
            }}));

            const scaledData = lineData.map(d => ({{
                year: xScale(d.year),          // Scale the year (x-axis)
                frequency: yScale(d.frequency) // Scale the frequency (y-axis)
            }}));

            const line = svg.append('path')
                .data([lineData])
                .attr('class', 'keyword-line')
                .attr('d', lineGenerator)
                .attr('stroke', colorScale(lineCount))
                .attr('stroke-width', 2)
                .attr('fill', 'none')

            updateLegend(keyword,lineCount);

            lineCount++;

      }}

      function updateLegend(keyword,lineCountx){{
        const legend = d3.select("#legend");

        // Create the legend item
        const legendItem = legend.append("div")
            .attr('class', 'legend-item')
            .style('display', 'flex')
            .style('align-items', 'center') // Align color box and text
            .style('margin', '0');         // Remove extra margins

        // Add the color square
        legendItem.append("div")
            .style('width', '20px')
            .style('height', '20px')
            .style('background-color', colorScale(lineCountx))
            .style('margin-right', '5px'); // Space between box and text

        // Add the text label
        legendItem.append("span")
            .text(keyword)
            .style('font-size', '12px');

      }}

      function updateLegendCat(s,lineCountx){{
        const legend = d3.select("#catLegend");

        // Create the legend item
        const legendItem = legend.append("div")
            .attr('class', 'legend-item')
            .style('display', 'flex')
            .style('align-items', 'center') // Align color box and text
            .style('margin', '0');         // Remove extra margins

        // Add the color square
        legendItem.append("div")
            .style('width', '20px')
            .style('height', '20px')
            .style('background-color', colorScale(lineCountx))
            .style('margin-right', '5px'); // Space between box and text

        // Add the text label
        legendItem.append("span")
            .text(s)
            .style('font-size', '9px');

      }}

        // Render the plot
        function updatePlotFreq() {{
            lineCount = 0;
            const year = +d3.select("#yearSliderFreq").property("value");
            const selectedSections = Array.from(document.querySelectorAll("#sections-freq input:checked")).map(d => d.value);
            const selectedSentiments = Array.from(document.querySelectorAll("#sentimentsfreq input:checked")).map(d => d.value);

            console.log(keywords);
            // Filter data
            const filteredData = data.filter(d =>
                d.pub_date <= year &&
                (selectedSections.includes("All")||selectedSections.includes(d.section)) &&
                selectedSentiments.includes(d.sentiment) &&
                (keywords.length === 0 || keywords.some(k => d.keywords.includes(k)))
            );

            // Aggregate data for display
            const yearCounts = {{}};
            const years = Array.from({{ length: 2024 - 2000 + 1 }}, (_, i) => 2000 + i);

            const maxYearCounts = {{}};
            years.forEach(y => {{
              maxYearCounts[y] = 0;
            }});

            keywords.forEach(k => {{
              years.forEach(y => {{
                yearCounts[y] = 0;
              }});
              filteredData.forEach(d => {{
                if (d.keywords.includes(k)) {{
                  yearCounts[d.pub_date] = (yearCounts[d.pub_date] || 0) + 1;
                }}
              }});
              years.forEach(y =>{{
                maxYearCounts[y] = Math.max(maxYearCounts[y], yearCounts[y]);
              }})

            }});

            const frequency = (Object.values(maxYearCounts)).map(Number);
            const maxFreq = Math.max(...frequency);

            paddedMaxFreq = maxFreq + 100;

            xScale = d3.scaleLinear()
                .domain([2000, year])
                .range([0, width]);

            yScale = d3.scaleLinear()
                .domain([0, paddedMaxFreq])
                .range([height, 0]);

            plotArea.selectAll(".grid").remove();
            plotArea.selectAll(".x-axis").remove();
            plotArea.selectAll(".y-axis").remove();
            svg.selectAll('.keyword-line').remove();

            const legend = d3.select("#legend");
            legend.html("");

            keywords.forEach(k => {{
              addKeywordLine(k,filteredData,year,selectedSections,selectedSentiments);
            }});

            // Re-add gridlines for the x-axis
            plotArea.append("g")
                .attr("class", "grid")
                .attr("transform", `translate(0,${{height}})`) // Position at the bottom of the plot area
                .call(d3.axisBottom(xScale)
                    .ticks(xScale.domain()[1] - xScale.domain()[0]) // Adjust for 1-unit spacing
                    .tickSize(-height) // Length of the grid lines
                    .tickFormat("")) // Hide tick labels
                .selectAll(".tick line")
                .attr("stroke", "gray") // Color of the gridlines
                .attr("stroke-opacity", 0.6) // Set opacity to 0.6
                .attr("shape-rendering", "crispEdges"); // For sharp grid lines

            // Re-add gridlines for the y-axis
            plotArea.append("g")
                .attr("class", "grid")
                .call(d3.axisLeft(yScale)
                    .ticks(5) // Adjust the number of ticks for y-axis
                    .tickSize(-width) // Length of the grid lines
                    .tickFormat("")) // Hide tick labels
                .selectAll(".tick line")
                .attr("stroke", "gray") // Color of the gridlines
                .attr("stroke-opacity", 0.6) // Set opacity to 0.6
                .attr("shape-rendering", "crispEdges"); // For sharp grid lines

            plotArea.append("g")
                .attr("class", "x-axis")
                .attr("transform", `translate(0, ${{height}})`)
                .transition()
                .duration(500)
                .call(d3.axisBottom(xScale).tickFormat(d3.format("d")));

            const tickCount = (paddedMaxFreq / 100) % 10 + 10;
            plotArea.append("g")
                .attr("class", "y-axis")
                .transition()
                .duration(500)
                .call(d3.axisLeft(yScale).ticks(tickCount));

            const articleListDiv = d3.select("#articleListFreq");
            articleListDiv.html("");
            if(keywords.length > 0){{
              updateArticleDisplayFreq(filteredData);
            }}

        }}

        function updateArticleDisplayFreq(filteredData) {{

            const keyword = d3.select("#keywordInputfreq").property("value").toLowerCase();
            const selectedSections = Array.from(document.querySelectorAll("#sections-freq input:checked")).map(d => d.value);
            const selectedSentiments = Array.from(document.querySelectorAll("#sentimentsfreq input:checked")).map(d => d.value);

            // Group articles by year
            const articlesByYear = d3.group(filteredData, d => {{
                // Ensure pub_date is converted to a string
                const year = typeof d.pub_date === 'number'
                    ? d.pub_date.toString()
                    : String(d.pub_date);
                return year;
            }});


            // Convert Map to object for easier logging
            const articlesByYearObj = {{}};
            articlesByYear.forEach((value, key) => {{
                articlesByYearObj[key] = value;
            }});

            const articleListDiv = d3.select("#articleListFreq");
            articleListDiv.html("");  // Clear previous entries

            // Iterate over each year group and create HTML structure
            Object.entries(articlesByYearObj).forEach(([year, articles]) => {{
                const yearDiv = articleListDiv.append("div").attr("class", "yearGroup");
                yearDiv.append("strong").text(year);  // Display the year

                articles.forEach(article => {{
                    const articleDiv = yearDiv.append("div").attr("class", "article");
                    articleDiv
                        .html(`&#8226; ${{article.headline}}`)
                        .style("color", article.sentiment === "Positive" ? "green" : "red")
                        .style("cursor", "pointer")
                        .on("mouseover", function() {{
                            // Show the URL when hovering over the title
                            d3.select(this).append("span").text(" - " + article.web_url).style("color", "blue");
                        }})
                        .on("mouseout", function() {{
                            // Remove the URL when not hovering
                            d3.select(this).select("span").remove();
                        }})
                        .on("click", function() {{
                            // Open the URL when the title is clicked
                            window.open(article.web_url, "_blank");
                        }});
                }});
            }});
            }}



        // Render the plot
        function updatePlotCat() {{
            lineCountCat = 0;
            const year = +d3.select("#yearSliderFreq").property("value");
            let selectedSections = Array.from(document.querySelectorAll("#sections-freq input:checked")).map(d => d.value);
            const selectedSentiments = Array.from(document.querySelectorAll("#sentimentsfreq input:checked")).map(d => d.value);

            if (selectedSections.includes("All")) {{
                selectedSections = uniqueSections;
              }}

            // Filter data
            const filteredData = data.filter(d =>
                d.pub_date <= year &&
                (selectedSections.includes(d.section)) &&
                selectedSentiments.includes(d.sentiment)
            );

            // Aggregate data for display
            const yearCounts = {{}};
            const years = Array.from({{ length: 2024 - 2000 + 1 }}, (_, i) => 2000 + i);

            const maxYearCounts = {{}};
            years.forEach(y => {{
              maxYearCounts[y] = 0;
            }});

            selectedSections.forEach(s => {{
              years.forEach(y => {{
                  yearCounts[y] = 0;
              }});
              filteredData.forEach(d => {{
                if (d.section === s) {{
                  yearCounts[d.pub_date] = (yearCounts[d.pub_date] || 0) + 1;
                }}
              }});
              years.forEach(y =>{{
                maxYearCounts[y] = Math.max(maxYearCounts[y], yearCounts[y]);
              }})

            }});

            const frequency = (Object.values(maxYearCounts)).map(Number);
            const maxFreqCat = Math.max(...frequency);

            paddedMaxFreqCat = maxFreqCat + 2;

            xScaleCat = d3.scaleLinear()
                .domain([2000, year])
                .range([0, width]);

            yScaleCat = d3.scaleLinear()
                .domain([0, paddedMaxFreqCat])
                .range([height, 0]);

            catPlotArea.selectAll(".grid").remove();
            catPlotArea.selectAll(".x-axis").remove();
            catPlotArea.selectAll(".y-axis").remove();
            svgCat.selectAll('.cat-line').remove();

            const legend = d3.select("#catLegend");
            legend.html("");

            selectedSections.forEach(k => {{
              addCatLine(k,filteredData,year,selectedSentiments);
            }});

            // Re-add gridlines for the x-axis
            catPlotArea.append("g")
                .attr("class", "grid")
                .attr("transform", `translate(0,${{height}})`) // Position at the bottom of the plot area
                .call(d3.axisBottom(xScaleCat)
                    .ticks(xScaleCat.domain()[1] - xScaleCat.domain()[0]) // Adjust for 1-unit spacing
                    .tickSize(-height) // Length of the grid lines
                    .tickFormat("")) // Hide tick labels
                .selectAll(".tick line")
                .attr("stroke", "gray") // Color of the gridlines
                .attr("stroke-opacity", 0.6) // Set opacity to 0.6
                .attr("shape-rendering", "crispEdges"); // For sharp grid lines

            // Re-add gridlines for the y-axis
            catPlotArea.append("g")
                .attr("class", "grid")
                .call(d3.axisLeft(yScaleCat)
                    .ticks(5) // Adjust the number of ticks for y-axis
                    .tickSize(-width) // Length of the grid lines
                    .tickFormat("")) // Hide tick labels
                .selectAll(".tick line")
                .attr("stroke", "gray") // Color of the gridlines
                .attr("stroke-opacity", 0.6) // Set opacity to 0.6
                .attr("shape-rendering", "crispEdges"); // For sharp grid lines

            catPlotArea.append("g")
                .attr("class", "x-axis")
                .attr("transform", `translate(0, ${{height}})`)
                .transition()
                .duration(500)
                .call(d3.axisBottom(xScaleCat).tickFormat(d3.format("d")));

            const tickCount = (paddedMaxFreqCat / 100) % 10 + 10;
            catPlotArea.append("g")
                .attr("class", "y-axis")
                .transition()
                .duration(500)
                .call(d3.axisLeft(yScaleCat).ticks(tickCount));

        }}


        function updateKeywordBox() {{
          const keywordBox = d3.select("#keywordBox");
          keywordBox.html(""); // Clear existing content
          keywords.forEach((keyword, index) => {{
              keywordBox
                  .append("span")
                  .style("display", "inline-block")
                  .style("margin", "2px")
                  .style("padding", "5px 10px")
                  .style("background-color", "#e0e0e0")
                  .style("border-radius", "5px")
                  .style("font-size", "14px")
                  .style("cursor", "default")
                  .html(`${{keyword}} <button data-index="${{index}}" style="margin-left: 5px; background-color: red; color: white; border: none; border-radius: 50%; width: 20px; height: 20px; cursor: pointer;">&times;</button>`);
          }});

          // Add event listeners to remove buttons
          d3.selectAll("#keywordBox button").on("click", function () {{
              const index = +this.getAttribute("data-index");
              keywords.splice(index, 1); // Remove keyword by index
              updateKeywordBox(); // Re-render keyword box
              updatePlot(); // Update plot
          }});
      }}


        // Initialize UI components
        const sectionsContainerfreq = d3.select("#sections-freq");

        // Add "All" checkbox first
        sectionsContainerfreq.append("label")
            .html('<input type="checkbox" id="allSectionsCheckboxFreq" value="All"> All');

        // Add section checkboxes
        sectionsContainerfreq.selectAll(".section-label")
            .data(uniqueSections)
            .enter()
            .append("label")
            .attr("class", "section-label")
            .html(d => `<input type="checkbox" class="section-checkbox" value="${{d}}"> ${{d}}`)
            .on("change", function(d) {{
                updatePlotFreq();
                updatePlotCat();
        }});


        d3.select("#yearSliderFreq").on("input", function () {{
            d3.select("#yearLabelFreq").text(this.value);
            updatePlotFreq();
            updatePlotCat();
        }});

        d3.selectAll("#sections-freq input, #sentimentsfreq input").on("change", function () {{
            updatePlotFreq();
            updatePlotCat();
        }});
        d3.select("#addKeywordButton").on("click", () => {{
          const input = d3.select("#keywordInputfreq");
          const keyword = input.property("value").trim().toLowerCase();
          if (keyword && !keywords.includes(keyword)) {{
              keywords.push(keyword); // Add unique keyword
              updateKeywordBox(); // Update keyword box
              updatePlotFreq();
          }}
          input.property("value", ""); // Clear input
        }});

        updatePlotFreq();
        updatePlotCat();


    </script>
</body>
</html>



"""

# Save to a file
current_path = os.getcwd()
file_name = "NYTSentimentVisualization.html"
full_path = os.path.join(current_path,file_name)

with open(full_path, 'w') as f:
    f.write(d3_html_code)