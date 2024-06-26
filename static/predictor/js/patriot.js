var margin = { top: 30, right: 50, bottom: 50, left: 30 },
        width = document.getElementById("patriot_div").offsetWidth - margin.left - margin.right,
        height = 400 - margin.top - margin.bottom;

var svg = d3.select('#patriot_map').append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
      .append('g')
        .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

async function get_current_filters() {
    var user = document.getElementById('user_select').value;
    var url = `/api/predictions`;

    svg.selectAll("*").remove();
    svg.append("text").text("Loading")

    var data = await d3.json(url);

    svg.selectAll("*").remove();

    data = data.filter(d => d.country == 'England').filter( d => d.score != null);

    var user_data = d3.rollups(
        data,
        val => d3.sum(val, x => x.score),
        d => d.user.username
    )
    .map(([k,v]) => ({user:k,goals:v}));

    user_data = d3.sort(user_data,(a,b) => d3.descending(a.goals,b.goals))



    var x = d3.scaleBand()
            .domain(user_data.map(d => d.user))
            .range([0,width])
            .padding(0.05)
    var y = d3.scaleLinear()
            .domain([0,user_data[0].goals])
            .range([height,0])

    svg.append("g")
        .attr("transform", `translate(0, ${height})`)
        .call(d3.axisBottom(x)).selectAll("text").attr("text-anchor", "start") 
        .attr("transform", "rotate(90) translate(10,-14)");

    svg.append("g")
        .call(d3.axisLeft(y));

    const myColor = d3.scaleSequential(d3.interpolatePlasma)
        .domain([0,d3.max(user_data,d=>d.goals)]);

    var tooltip = d3.select("#goals_map")
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
          .style("opacity", 0.5);
  
      }
      var mousemove = function(mouse,d) {
        tooltip.html( `${d.user} says ${d.goals} for England`)
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
        .data(user_data)
        .join("rect")
            .attr("x", d => x(d.user))
            .attr("y", d => y(d.goals))
            .attr("width", x.bandwidth())
            .attr("height", d =>  height - y(d.goals))
            .style("fill",  (d)  => myColor(d.goals))
            .on("mouseover", mouseover)
            .on("mousemove", mousemove)
            .on("mouseleave", mouseleave);

    svg.append("text")
          .attr("class", "y label")
          .attr("text-anchor", "end")
          .attr("y", 6)
          .attr("x", 0)
          .attr("dy", ".75em")
          .attr("transform", "rotate(-90) translate(0,-40)")
          .text("Goals");

}

document.getElementById('user_select').addEventListener('change',get_current_filters);
// get_current_filters()