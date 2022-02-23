var i;
var cs = document.getElementsByClassName("tool");
for (i = 0; i < cs.length; i++) {
  var points =  Math.round($("#tool"+i).data('temp'));
  var maxPoints =  Math.round($("#tool"+i).data('max'));
  var percent = points / maxPoints * 100;
  var ratio = percent / 100;
  var pie = d3.layout
    .pie()
    .value(function(d) {
      return d;
    })
    .sort(null);
  var w = 80,
    h = 80;
  var outerRadius = w / 2 - 10;
  var innerRadius = 40;
  var color = ["#ececec", "rgba(69,180,73,1)", "#888888"];
  var colorOld = "#F00";
  var colorNew = "#0F0";
  var arc = d3.svg
    .arc()
    .innerRadius(innerRadius)
    .outerRadius(outerRadius)
    .startAngle(0)
    .endAngle(Math.PI);

  var arcLine = d3.svg
    .arc()
    .innerRadius(innerRadius)
    .outerRadius(outerRadius)
    .startAngle(0);



  var svg = d3
    .select("#tool"+i)
    .append("svg")
    .attr({
      width: w,
      height: h
    })
    .append("g")
    .attr({
      transform: "translate(" + w / 2 + "," + h / 2 + ")"
    });

  var path = svg
    .append("path")
    .attr({
      d: arc,
      transform: "rotate(-90)"
    })
    .style({
      fill: color[0]
    });

  var pathForeground = svg
    .append("path")
    .datum({ endAngle: 0 })
    .attr({
      class: "loadfill",
      d: arcLine,
      transform: "rotate(-90)"
    })
    .style({
      fill: function(d, i) {
        return color[1];
      }
    });

  var middleCount = svg
    .append("text")
    .datum(0)
    .text(function(d) {
      return points;
    })
    .attr({
      class: "middleText",
      "text-anchor": "middle",
      dy: 0,
      dx: 1
    })
    .style({
      fill: d3.rgb("#000000"),
      "font-size": "20px"
    });

  var oldValue = 0;
  var arcTween = function(transition, newValue, oldValue) {

    transition.attrTween("d", function(d) {
      var interpolate = d3.interpolate(d.endAngle, Math.PI * (newValue / 100));
      var interpolateCount = d3.interpolate(oldValue, newValue);

      return function(t) {
        d.endAngle = interpolate(t);
        // change percentage to points before rendering text
        middleCount.text(Math.floor(interpolateCount(t)/100*maxPoints));

        return arcLine(d);
      };
    });
  };

  pathForeground
    .transition()
    .duration(750)
    .ease("cubic")
    .call(arcTween, percent, oldValue, points);

}
