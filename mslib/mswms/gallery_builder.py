"""
    mslib.mswms.gallery_builder
    ~~~~~~~~~~~~~~~~~~~

    This module contains functions for generating the static/docs/plots.js file, aka the gallery.

    This file is part of mss.

    :copyright: Copyright 2021 May Bär
    :copyright: Copyright 2021 by the mss team, see AUTHORS.
    :license: APACHE-2.0, see LICENSE for details.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import os
from PIL import Image
import io
from matplotlib import pyplot as plt
import defusedxml.ElementTree as etree
import inspect
from mslib.mswms.mpl_vsec import AbstractVerticalSectionStyle
from mslib.mswms.mpl_lsec import AbstractLinearSectionStyle


static_location = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")

begin = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {font-family: Arial;}

.gtooltip {
  position: relative;
  display: inline-block;
}

.gallery .gtooltiptext {
  visibility: hidden;
  width: 400px;
  background-color: lavender;
  border: 1px solid #000;
  text-align: center;
  border-radius: 6px;
  padding: 5px 0;
  position: absolute;
  z-index: 1;
  top: 150%;
  left: 50%;
  margin-left: -200px;
}

.gallery .gtooltiptext::after {
  content: "";
  position: absolute;
  bottom: 100%;
  left: 50%;
  margin-left: -5px;
  border-width: 5px;
  border-style: solid;
  border-color: transparent transparent black transparent;
}

.gallery:hover .gtooltiptext {
  visibility: visible;
}

/* Style the tab */
.tab {
  overflow: hidden;
  border: 1px solid #DDDDFF;
  background-color: #E6E6FA;
}

/* Style the buttons inside the tab */
.tab button {
  background-color: inherit;
  float: left;
  border: none;
  outline: none;
  cursor: pointer;
  padding: 14px 16px;
  transition: 0.3s;
  font-size: 17px;
}

/* Change background color of buttons on hover */
.tab button:hover {
  background-color: #DDDDFF;
}

/* Create an active/current tablink class */
.tab button.active {
  background-color: #CCCCFF;
}

/* Style the tab content */
.tabcontent {
  display: none;
  padding: 6px 12px;
  -webkit-animation: fadeEffect 1s;
  animation: fadeEffect 1s;
}

.tabcontent::after {
  content: "";
  clear: both;
  display: block;
  float: none;
}

/* Style the plots content */
div.gallery {
  text-align: center;
  margin: 0.5%;
  border: 1px solid #ccc;
  float: left;
  width: 24%;
  box-shadow: 0 0 2px 1px rgba(0, 0, 0, 0.2);
  transition: box-shadow 0.3s ease-in-out;
}

div.gallery:hover {
  box-shadow: 0 0 5px 1px rgba(0, 0, 255, 0.5);
}

div.gallery img {
  width: 100%;
  height: auto;
}

/* Fade in tabs */
@-webkit-keyframes fadeEffect {
  from {opacity: 0;}
  to {opacity: 1;}
}

@keyframes fadeEffect {
  from {opacity: 0;}
  to {opacity: 1;}
}
</style>
</head>
<body>

<h3>Plot Gallery</h3>

<div class="tab">
  <button class="tablinks active" onclick="openTab(event, 'Top View')">Top Views</button>
  <button class="tablinks" onclick="openTab(event, 'Side View')">Side Views</button>
  <button class="tablinks" onclick="openTab(event, 'Linear View')">Linear Views</button>
</div>
"""

plots = {"Top": [], "Side": [], "Linear": []}

end = """
<script>
function openTab(evt, tabName) {
  close = evt.currentTarget.className.includes("active")

  var i, tabcontent, tablinks;
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }
  tablinks = document.getElementsByClassName("tablinks");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }

  if(!close){
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
  }
}
</script>
</body>
</html>
"""


def image_md(image_location, caption="", link=None, tooltip=""):
    """
    Returns the html code for the individual plot
    """
    image = f"""
    <a href="{link}">
     <img src="{image_location}" style="width:100%"/>
    </a>""" if link else f"""<img src="{image_location}" style="width: 100 % "/>"""
    return f"""<div class="gallery">
                 {image}
                 <div class="gtooltip">
                  {caption}<span class="gtooltiptext">{tooltip}</span>
                 </div>
                </div>"""


def write_js():
    """
    Writes the static/docs/plots.js file containing the gallery
    """
    js = begin
    for l_type in plots:
        style = ""
        if l_type == "Top":
            style = "style=\"display: block;\""
        js += f"<div id=\"{l_type} View\" class=\"tabcontent\" {style}>"
        js += "\n".join(plots[l_type])
        js += "</div>"

    with open(os.path.join(static_location, "docs", "plots.js"), "w+") as md:
        md.write(js + end)


def write_plot_details(plot_object, l_type="top"):
    """
    Extracts and writes the plots code files at static/code/*
    """
    if not os.path.exists(os.path.join(static_location, "code")):
        os.mkdir(os.path.join(static_location, "code"))
    with open(os.path.join(static_location, "code", f"{l_type}_{plot_object.name}.md"), "w+") as md:
        md.write(f"Requires datafields: {', '.join(f'`{field[1]}`' for field in plot_object.required_datafields)}\n\n")
        md.write("\t" + "\t".join(inspect.getsource(type(plot_object)).splitlines(True)))


def create_linear_plot(xml, file_location):
    """
    Draws a plot of the linear .xml output
    """
    data = xml.find("Data")
    values = [float(value) for value in data.text.split(",")]
    unit = data.attrib["unit"]
    numpoints = int(data.attrib["num_waypoints"])
    fig = plt.figure(dpi=80, figsize=[800 / 80, 600 / 80])
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(range(numpoints), values)
    ax.set_ylabel(unit)
    fig.savefig(file_location)


def add_image(plot, plot_object, generate_code=False):
    """
    Adds the images to the static/plots/* folder and generates the html codes to display them
    """
    l_type = "Linear" if isinstance(plot_object, AbstractLinearSectionStyle) else \
        "Side" if isinstance(plot_object, AbstractVerticalSectionStyle) else "Top"

    if plot:
        if not os.path.exists(os.path.join(static_location, "plots")):
            os.mkdir(os.path.join(static_location, "plots"))
        if l_type == "Linear":
            create_linear_plot(etree.fromstring(plot), os.path.join(static_location, "plots", l_type + "_" +
                                                                    plot_object.name + ".png"))
        else:
            with Image.open(io.BytesIO(plot)) as image:
                image.save(os.path.join(static_location, "plots", l_type + "_" + plot_object.name + ".png"),
                           format="PNG")

    if generate_code:
        write_plot_details(plot_object, l_type)

    plots[l_type].append(image_md(f"/static/plots/{l_type}_{plot_object.name}.png", plot_object.name,
                                  f"/mss/code?filename={l_type}_{plot_object.name}.md" if generate_code else None,
                                  f"{plot_object.title}" + (f"<br>{plot_object.abstract}"
                                                            if plot_object.abstract else "")))
