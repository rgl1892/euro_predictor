var margin = { top: 30, right: 50, bottom: 50, left: 50 },
  width =
    document.getElementById("points_div").offsetWidth -
    margin.left -
    margin.right,
  height = 400 - margin.top - margin.bottom;

var svg = d3
  .select("#points_map")
  .append("svg")
  .attr("width", width + margin.left + margin.right)
  .attr("height", height + margin.top + margin.bottom)
  .append("g")
  .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

async function get_current_filters() {
  var user = document.getElementById("user_select").value;
  var url = `api/predictions?user=${user}`;

  svg.selectAll("*").remove();
  svg.append("text").text("Loading");
  var data = await d3.json(url);
  svg.selectAll("*").remove();
  data = d3.filter(data, (d) => d.score != null);
  data = d3.filter(data, (d) => d.user.username != "Actual_Scores");
  data = d3.filter(data, (d) => d.match_choice.home_away == "Home");

  data = d3.rollups(
    data,
    (v) => d3.sum(v, (d) => d.points),
    (d) => d.user.username,
    (d) => d.match_choice.match_number.match_number
  );

  data = d3.map(data, (d) => [d[0], d3.cumsum(d[1], (e) => e[1]),d3.sum(d[1],d=>d[1])]);
  var max_points = d3.max(data,d => d[2]);

  const y = d3.scaleLinear().domain([0, max_points]).nice().range([height, 0]);

  const x = d3.scaleLinear().domain([0, 51]).range([0, width]);

  svg
    .append("g")
    .attr("transform", `translate(0, ${height})`)
    .call(d3.axisBottom(x));

  svg.append("g").call(d3.axisLeft(y));

  const myColor = d3.scaleSequential(d3.interpolatePlasma)
                .domain([0,max_points]);

  
  const line = d3.line()
  .x((d,i) => x(i+1))
  .y((d,i) => y(d)).curve(d3.curveBasis);

  var tooltip = d3.select("#points_map")
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
        .attr('stroke-width', 4)
          .style("opacity", 1);
  
      }
      var mousemove = function(mouse,d) {

        tooltip.html(d[0])
          .style("left", `${mouse["layerX"] + 20}px`)
          .style("top", `${mouse["layerY"] - 20}px`);
      }
      var mouseleave = function(d) {
        tooltip
          .style("opacity", 0);
        d3.select(this)
          .attr('stroke-width', 2)
          .style("opacity", 0.8)}

svg.append("g")
  .selectAll('.line')
  .data(data)
  .join('path')
    .attr('class', 'line')
    .attr('fill', 'none')
    .attr('stroke', (d)  => myColor(d[2]))

    .attr('opacity', 0.8)

    .attr('stroke-width', 2)
    .attr('d', d => line(d[1]))
    .on("mouseover", mouseover)
    .on("mousemove", mousemove)
    .on("mouseleave", mouseleave);
}

document
  .getElementById("user_select")
  .addEventListener("change", get_current_filters);

  get_current_filters()