var margin = { top: 30, right: 50, bottom: 50, left: 50 },
        width = document.getElementById("goal_div").offsetWidth - margin.left - margin.right,
        height = 400 - margin.top - margin.bottom;

var svg = d3.select('#goals_map').append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
      .append('g')
        .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

async function get_current_filters() {
    var user = document.getElementById('user_select').value;
    var url = `api/predictions?user=${user}`;

    svg.selectAll("*").remove();
    svg.append("text").text("Loading")
    var data = await d3.json(url);
    svg.selectAll("*").remove();


    data = d3.filter(data, d => d.score != null);
    var country = d3.rollups(
        data,
        val => d3.sum(val, x => x.score),
        d => d.country
    )
    .map(([k,v]) => ({country:k,goals:v}));

    country = d3.sort(country,(a,b) => d3.descending(a.goals,b.goals));
    
    var x = d3.scaleBand()
            .domain(country.map(d => d.country.slice(0,3)))
            .range([0,width])
            .padding(0.05)
    var y = d3.scaleLinear()
            .domain([0,country[0].goals])
            .range([height,0])

    svg.append("g")
        .attr("transform", `translate(0, ${height})`)
        .call(d3.axisBottom(x));
    svg.append("g")
        .call(d3.axisLeft(y));

    const myColor = d3.scaleSequential(d3.interpolatePlasma)
        .domain([0,d3.max(country,d=>d.goals)]);
    
    svg.selectAll("mybar")
        .data(country)
        .enter()
        .append("rect")
            .attr("x", d => x(d.country.slice(0,3)))
            .attr("y", d => y(d.goals))
            .attr("width", x.bandwidth())
            .attr("height", d =>  height - y(d.goals))
            .style("fill",  (d)  => myColor(d.goals))
            .append("svg:title")
            .text((d) => `${d.country}: ${d.goals}`)

     svg.append("text")
            .attr("class", "x label")
            .attr("text-anchor", "end")
            .attr("x", width)
            .attr("y", height + 40)
            .text("Country");

    svg.append("text")
          .attr("class", "y label")
          .attr("text-anchor", "end")
          .attr("y", 6)
          .attr("x", 0)
          .attr("dy", ".75em")
          .attr("transform", "rotate(-90) translate(0,-40)")
          .text("Goals");
    
}


document.getElementById('user_select').addEventListener('change',get_current_filters)