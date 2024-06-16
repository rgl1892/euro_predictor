var margin = { top: 30, right: 50, bottom: 50, left: 30 },
        width = document.getElementById("heat_div").offsetWidth - margin.left - margin.right,
        height = 400 - margin.top - margin.bottom;

var svg = d3.select('#heat_map').append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
      .append('g')
        .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

async function get_current_filters() {
    var user = document.getElementById('user_select').value;
    var match_choice = document.getElementById('match').value;
    var url = `api/predictions?user=${user}&match_choice__match_number=${match_choice}`;
    var actual_url = `api/predictions?user=7&match_choice__match_number=${match_choice}`;

    svg.selectAll("*").remove();
    svg.append("text").text("Loading")

    var data = await d3.json(url);
    var actual_data = await d3.json(actual_url);
    var actual_home = d3.filter(actual_data, d => d.score != null && d.match_choice.home_away == 'Home');
    var actual_away = d3.filter(actual_data, d => d.score != null && d.match_choice.home_away == 'Away');
    var actual_scores = d3.transpose([d3.map(actual_home,d => d.score),d3.map(actual_away,d => d.score)]);
    var actual_newArray = [];
      for(var element of actual_scores){
          if(typeof actual_newArray[JSON.stringify(element)] === 'undefined' || actual_newArray[JSON.stringify(element)] === null){
            actual_newArray[JSON.stringify(element)] = 1;
          }else{
            actual_newArray[JSON.stringify(element)] +=1;
          }
        }
        var actual_result = Object.keys(actual_newArray).map(key => ({
          item: JSON.parse(key),
          count: actual_newArray[key]
        }));  
    data = d3.filter(data, d => d.user.username != 'Actual_Scores');

    svg.selectAll("*").remove();

    var home = d3.filter(data, d => d.score != null && d.match_choice.home_away == 'Home');
    
    var away = d3.filter(data, d => d.score != null && d.match_choice.home_away == 'Away');
    
    var scores = d3.transpose([d3.map(home,d => d.score),d3.map(away,d => d.score)]);
    
    
    var newArray = [];
    for(var element of scores){
        if(typeof newArray[JSON.stringify(element)] === 'undefined' || newArray[JSON.stringify(element)] === null){
          newArray[JSON.stringify(element)] = 1;
        }else{
          newArray[JSON.stringify(element)] +=1;
        }
      }
      var result = Object.keys(newArray).map(key => ({
        item: JSON.parse(key),
        count: newArray[key]
      }));   
      var actual_newArray = [];
      for(var element of actual_scores){
          if(typeof actual_newArray[JSON.stringify(element)] === 'undefined' || actual_newArray[JSON.stringify(element)] === null){
            actual_newArray[JSON.stringify(element)] = 1;
          }else{
            actual_newArray[JSON.stringify(element)] +=1;
          }
        }
        var actual_result = Object.keys(actual_newArray).map(key => ({
          item: JSON.parse(key),
          count: actual_newArray[key]
        }));  

    

    var x = d3.scaleBand()
            .range([0,width])
            .domain([0,1,2,3,4,5,6])
            .padding(0.05);
    svg.append("g")
        .attr("transform", `translate(0, ${height})`)
      .call(d3.axisBottom(x));

    var y = d3.scaleBand()
      .range([height,0])
      .domain([0,1,2,3,4,5,6])
      .padding(0.05);
    svg.append("g")
      .call(d3.axisLeft(y));

    const myColor = d3.scaleSequential(d3.interpolatePlasma)
      .domain([0,d3.max(result,d=>d.count)]);

    svg.append("text")
      .attr("class", "x label")
      .attr("text-anchor", "end")
      .attr("x", width)
      .attr("y", height + 40)
      .text(`${home[0].country}`);
    svg.append("text")
    .attr("class", "y label")
    .attr("text-anchor", "end")
    .attr("y", 6)
    .attr("x", 0)
    .attr("dy", ".75em")
    .attr("transform", "rotate(-90)")
    .text(`${away[0].country}`);

    var tooltip = d3.select("#heat_map")
      .append("div")
      .style("opacity", 0)
      .attr("class", "tooltip")
      .style("background-color", "white")
      .style("border", "solid")
      .style("border-width", "2px")
      .style("border-radius", "5px")
      .style("padding", "5px")
      .style("position", "absolute");

    var mouseover = function(d) {
      tooltip.style("opacity", 1);
      d3.select(this)
        .style("stroke", "black")
        .style("opacity", 0.8);

    }
    var mousemove = function(mouse,d) {
      tooltip.html( `${d.count} : ${d.item[0]}-${d.item[1]}`)
        .style("left", `${mouse["layerX"] + 20}px`)
        .style("top", `${mouse["layerY"] - 20}px`);
    }
    var actual_mousemove = function(mouse,d) {
      tooltip.html( `Actual Score : ${d.item[0]}-${d.item[1]}`)
        .style("left", `${mouse["layerX"] + 20}px`)
        .style("top", `${mouse["layerY"] - 20}px`);
    }
    var mouseleave = function(d) {
      tooltip
        .style("opacity", 0);
      d3.select(this)
        .style("stroke", "none")
        .style("opacity", 1)}

    svg.selectAll("rect")
      .data(result)
      .join("rect")
      .attr("x", function(d) { return x(d.item[0]) })
      .attr("y", function(d) { return y(d.item[1]) })
      .attr("rx", 4)
      .attr("ry", 4)
      .attr("width", x.bandwidth() )
      .attr("height", y.bandwidth() )
      .style("fill", function(d) { return myColor(d.count)} )
    .on("mouseover", mouseover)
    .on("mousemove", mousemove)
    .on("mouseleave", mouseleave);

  
    svg.selectAll("circle")
      .data(actual_result)
      .join("circle")
      .attr("cx", function(d) { return x(d.item[0]) + x.bandwidth()/2 })
      .attr("cy", function(d) { return y(d.item[1]) + y.bandwidth()/2 })
      .attr("r", 12 )
      .style("fill", "white" )
    .on("mouseover", mouseover)
    .on("mousemove", actual_mousemove)
    .on("mouseleave", mouseleave);
}


document.getElementById('user_select').addEventListener('change',get_current_filters);
document.getElementById('match').addEventListener('change',get_current_filters);

