"""
    mslib.mswms.gallery_builder
    ~~~~~~~~~~~~~~~~~~~

    This module contains functions for generating the plots.html file, aka the gallery.

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
import logging
from matplotlib import pyplot as plt
import defusedxml.ElementTree as etree
import inspect
from mslib.mswms.mpl_vsec import AbstractVerticalSectionStyle
from mslib.mswms.mpl_lsec import AbstractLinearSectionStyle

STATIC_LOCATION = ""
try:
    import mss_wms_settings
    if hasattr(mss_wms_settings, "_gallerypath"):
        STATIC_LOCATION = mss_wms_settings._gallerypath
    else:
        STATIC_LOCATION = os.path.join(os.path.dirname(os.path.abspath(mss_wms_settings.__file__)), "gallery")
except ImportError as e:
    logging.warning(f"{e}. Can't generate gallery.")

DOCS_LOCATION = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs", "gallery")


code_header = """\"\"\"
    This file is part of mss.

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
\"\"\"

"""

begin = """
<!DOCTYPE html>
<html>
<head>
<style>

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

.tab input[type=text]{
  float: right;
  padding: 6px;
  border: 2px solid #DDDDFF;
  margin-top: 8px;
  margin-right: 16px;
  font-size: 17px;
}

.tab select{
  float: right;
  padding: 6px;
  border: 2px solid #DDDDFF;
  background-color: #F7F7F7;
  margin-top: 8px;
  margin-right: 16px;
  font-size: 17px;
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
<body onload="hideEmptySelects();
              if(document.getElementById('level-select').options.length > 0)
                document.getElementById('level-select').options[0].selected = 'selected';
              if(document.getElementById('time-select').options.length > 0)
                document.getElementById('time-select').options[0].selected = 'selected';
              document.getElementById('gallery-filter').value = '';
              changeImages();">

<h3>Plot Gallery</h3>

<div class="tab">
  <button class="tablinks active" onclick="openTab(event, 'Top-View')">Top Views</button>
  <button class="tablinks" onclick="openTab(event, 'Side-View')">Side Views</button>
  <button class="tablinks" onclick="openTab(event, 'Linear-View')">Linear Views</button>
  <input type="text" placeholder="Search..." id="gallery-filter" oninput="filterContent()"></input>
  <select name="levels" id="level-select" onchange="changeImages()"></select>
  <select name="times" id="time-select" onchange="changeImages()"></select>
</div>
"""

plots = {"Top": [], "Side": [], "Linear": []}
plot_htmls = {}

end = """
<script>
files = [];

function hideEmptySelects(){
    levels = document.getElementById("level-select");
    times = document.getElementById("time-select");
    selects = [levels, times];
    for(var select of selects){
        if(select && select.children.length == 0){
            select.style.display = "none";
        }
    }
}

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

function imageExists(image_url){
    return files.includes(image_url.split("/").pop());
}

function changeImages(from_filter=false){
    if(!from_filter){
        filterContent();
        return;
    }

    var value = document.getElementById("level-select").value;
    value = value != "" ? value : "None";
    var vtime = document.getElementById("time-select").value
                .replaceAll(" ", "_").replaceAll(":", "_").replaceAll("-", "_");
    vtime = vtime != "" ? vtime : "None";
    var itime = "None";
    if(vtime != "None"){
        selected = document.getElementById("time-select").options[document.getElementById("time-select").selectedIndex]
        var itime = selected.parentNode.label.replaceAll(" ", "_").replaceAll(":", "_").replaceAll("-", "_");
    }

    hrefs = document.getElementsByName("gallery-href");
    images = document.getElementsByName("gallery-image");
    for(var i = 0; i < images.length; i++){
        var image = images[i];
        var tmpLevel = value.replaceAll(" ", "");
        var new_location = image.src.replace(image.src.split("-").pop(), `${tmpLevel}it${itime}vt${vtime}.png`);
        var parentNode = hrefs.length == images.length ? image.parentNode.parentNode : image.parentNode;

        parentNode.style.display = "block";

        if(!imageExists(new_location)){
            if(image.src.includes("Top")){
                parentNode.style.display = "none";
                continue;
            }
            tmpLevel = image.src.split("-").pop().split("it")[0];
            new_location = image.src.replace(image.src.split("-").pop(), `${tmpLevel}it${itime}vt${vtime}.png`)
        }
        var exists = imageExists(new_location);
        if(exists){
            image.src = new_location;
        }
    }
}

function filterContent(){
    input = document.getElementById("gallery-filter").value;
    elements = document.getElementsByClassName("gallery");
    for(var i = 0; i < elements.length; i++){
        for(var j = 0; j < elements[i].childNodes.length; j++){
            if(elements[i].childNodes[j].className == "gtooltip"){
                if(!elements[i].childNodes[j].firstChild.nodeValue.toLowerCase().includes(input.toLowerCase())){
                    elements[i].style.display = "none";
                } else {
                    elements[i].style.display = "block";
                }
            }
        }
    }

    changeImages(true);
}
</script>
</body>
</html>
"""

plot_html_begin = """
   <select name="levels" id="level-select" onchange="changeImages()"></select>
   <select name="times" id="time-select" onchange="changeImages()"></select>
   <script>
   hideEmptySelects();
   if(document.getElementById('level-select').options.length > 0)
      document.getElementById('level-select').options[0].selected = 'selected';
   if(document.getElementById('time-select').options.length > 0)
      document.getElementById('time-select').options[0].selected = 'selected';
   changeImages();

   function hideEmptySelects(){
      levels = document.getElementById("level-select");
      times = document.getElementById("time-select");
      selects = [levels, times];
      for(var select of selects){
         if(select && select.children.length == 0){
            select.style.display = "none";
         }
      }
   }

   function changeImages(){
       var value = document.getElementById("level-select").value;
       value = value != "" ? value : "None";
       var vtime = document.getElementById("time-select").value
                   .replaceAll(" ", "_").replaceAll(":", "_").replaceAll("-", "_");
       vtime = vtime != "" ? vtime : "None";
       var itime = "None";
       if(vtime != "None"){
         selected = document.getElementById("time-select").options[document.getElementById("time-select").selectedIndex]
         var itime = selected.parentNode.label.replaceAll(" ", "_").replaceAll(":", "_").replaceAll("-", "_");
       }

       images = document.getElementsByTagName("img");
       for(var i = 0; i < images.length; i++){
           var image = images[i];
           if(image.src.includes("Top_") || image.src.includes("Side_") || image.src.includes("Linear_")){
              var tmpLevel = value.replaceAll(" ", "");
              var new_location = image.src.replace(image.src.split("-").pop(), `${tmpLevel}it${itime}vt${vtime}.png`);
              new_location = new_location.replace("_images", "_static");
              image.src = new_location;
           }
       }
   }</script>

"""


def image_md(image_location, caption="", link=None, tooltip=""):
    """
    Returns the html code for the individual plot
    """
    image = f"""
    <a href="{link}" name="gallery-href">
     <img src="{image_location}" name="gallery-image" alt="{tooltip}"
     style="width:100%" id="{"".join(image_location.split("-")[:-1])}"/>
    </a>""" if link else f"""<img src="{image_location}" name="gallery-image" style="width: 100 % "
    id="{"".join(image_location.split("-")[:-1])}"/>"""
    return f"""<div class="gallery">
                 {image}
                 <div class="gtooltip">
                  {caption}<span class="gtooltiptext">{tooltip}</span>
                 </div>
                </div>"""


def write_doc_index():
    """
    Write index containing all code examples for the sphinx docs
    """
    with open(os.path.join(DOCS_LOCATION, "code", "index.rst"), "w+") as rst:
        files = "\n".join(sorted(["   " + f[:-4] for f in os.listdir(os.path.join(DOCS_LOCATION, "code"))
                                  if "index" not in f and ".rst" in f]))
        rst.write(f"""
Code Examples
--------------

.. toctree::

{files}
""")


def write_code_pages(sphinx=False, url_prefix=None):
    """
    Writes the .html, .rst or .md files containing the code examples for the plots
    """
    from mslib.index import SCRIPT_NAME
    for layer in plot_htmls:
        code_path = f"code/{layer}.html" if sphinx \
            else f"{url_prefix if url_prefix else ''}{SCRIPT_NAME}mss/code/{layer}.md"
        if not sphinx:
            with open(os.path.join(STATIC_LOCATION, "code", code_path.split('/')[-1]), "w+") as f:
                f.write(plot_htmls[layer])
        else:
            with open(os.path.join(DOCS_LOCATION, "code", code_path.split('/')[-1].replace("html", "rst")), "w+") as f:
                f.write(f""".. raw:: html\n\n{plot_htmls[layer]}""")


def write_html(sphinx=False):
    """
    Writes the plots.html file containing the gallery
    """
    location = DOCS_LOCATION if sphinx else STATIC_LOCATION
    html = begin
    if sphinx:
        html = html.replace("<h3>Plot Gallery</h3>", "")

    for l_type in plots:
        style = ""
        if l_type == "Top":
            style = "style=\"display: block;\""
        html += f"<div id=\"{l_type}-View\" class=\"tabcontent\" {style}>"
        html += "\n".join(plots[l_type])
        html += "</div>"

    with open(os.path.join(location, "plots.html"), "w+") as file:
        file.write(html + end)
        logging.info(f"plots.html created at {os.path.join(location, 'plots.html')}")


def import_instructions(plot_object, l_type, layer, native_import=None, dataset=""):
    """
    Returns instructions on how to import the plot object, or None if not yet implemented
    """
    # Imports here due to some circular import issue if imported too soon
    from mslib.mswms.mpl_lsec_styles import LS_DefaultStyle
    from mslib.mswms.mpl_vsec_styles import VS_GenericStyle
    from mslib.mswms.mpl_hsec_styles import HS_GenericStyle

    from_text = f"{l_type}_{dataset}{plot_object.name}" if not native_import else native_import
    instruction = f"from {from_text} import {plot_object.__class__.__name__}\n" \
                  f"register_{layer}_layers = [] if not register_{layer}_layers else register_{layer}_layers\n"
    # Generic LS class
    if isinstance(plot_object, LS_DefaultStyle):
        instruction += f"register_{layer}_layers.append(({plot_object.__class__.__name__}, " \
                       f"\"{plot_object.required_datafields[-1][1]}\", \"{plot_object.required_datafields[-1][0]}\", " \
                       f"[next(iter(data))]))"
    # Generic HS or VS class without custom _prepare_datafields
    elif (isinstance(plot_object, VS_GenericStyle) or isinstance(plot_object, HS_GenericStyle)) and "pass" in \
            inspect.getsource(plot_object._prepare_datafields):
        style = "hsec" if isinstance(plot_object, HS_GenericStyle) else "vsec"

        # Convert range to list, since numpy arrays string representation is unparseable
        if plot_object.contours:
            for i in range(len(plot_object.contours)):
                temp = list(plot_object.contours[i])
                if len(temp) > 1 and temp[1] is not None:
                    temp[1] = list(temp[1])
                    plot_object.contours[i] = tuple(temp)

        instruction = f"from mslib.mswms import mpl_{style}_styles\n"
        instruction += f"name = \"{plot_object.__class__.__name__}\"\n" \
                       f"ent = \"{plot_object.dataname if hasattr(plot_object, 'dataname') else None}\"\n" \
                       f"vtype = \"{plot_object.required_datafields[0][0]}\"\n" \
                       f"add_data = " \
                       f"{plot_object.required_datafields[1:] if len(plot_object.required_datafields) > 1 else None}\n"\
                       f"fix_style = {plot_object.styles}\n" \
                       f"contours = {plot_object.contours}\n"
        instruction += f"mpl_{style}_styles.make_generic_class(name, ent, vtype, add_data, contours, fix_style)\n"
        instruction += f"register_{layer}_layers.append((" \
                       f"getattr(mpl_{style}_styles, \"{plot_object.__class__.__name__}\"), [next(iter(data))]))"
    # Normal non-generic class
    else:
        instruction += f"register_{layer}_layers.append(({plot_object.__class__.__name__}, [next(iter(data))]))"

    return instruction


def source_and_import(plot_object, l_type, layer, dataset=""):
    """
    Returns the source code and import instructions for the plot_object
    """
    # Imports here due to some circular import issue if imported too soon
    from mslib.mswms.mpl_lsec_styles import LS_DefaultStyle
    from mslib.mswms.mpl_vsec_styles import VS_GenericStyle
    from mslib.mswms.mpl_hsec_styles import HS_GenericStyle

    native_import = "mslib" + \
                    os.path.abspath(inspect.getfile(type(plot_object))).split("mslib")[-1].replace(os.sep, ".")[:-3] \
        if os.path.join("mslib", "mswms") in os.path.abspath(inspect.getfile(type(plot_object))) \
        and not ((isinstance(plot_object, HS_GenericStyle) or isinstance(plot_object, VS_GenericStyle)) and
                        "pass" not in inspect.getsource(plot_object._prepare_datafields)) else None

    import_text = import_instructions(plot_object, l_type, layer, dataset=dataset)
    import_text_native = import_instructions(plot_object, l_type, layer, native_import, dataset) \
        if native_import else None

    modules = [m for m in inspect.getsource(inspect.getmodule(type(plot_object))).splitlines()
               if m.startswith("import") or m.startswith("from")]
    source = code_header + "\n".join(modules) + "\n"
    # Normal class, not generic
    if not isinstance(plot_object, VS_GenericStyle) and not isinstance(plot_object, HS_GenericStyle) and \
            not isinstance(plot_object, LS_DefaultStyle):
        source += "\n" + "".join(inspect.getsource(type(plot_object)).splitlines(True))
    # Generic VS or HS class with custom _prepare_datafields
    elif not isinstance(plot_object, LS_DefaultStyle) and \
            "pass" not in inspect.getsource(plot_object._prepare_datafields):
        parent = "HS_GenericStyle" if isinstance(plot_object, HS_GenericStyle) else "VS_GenericStyle"
        style = "hsec" if isinstance(plot_object, HS_GenericStyle) else "vsec"

        # Convert range to list, since numpy arrays string representation is unparseable
        if plot_object.contours:
            for i in range(len(plot_object.contours)):
                temp = list(plot_object.contours[i])
                if len(temp) > 1 and temp[1] is not None:
                    temp[1] = list(temp[1])
                    plot_object.contours[i] = tuple(temp)

        source += f"from mslib.mswms.mpl_{style}_styles import {parent}\n\n"
        prepare = inspect.getsource(plot_object._prepare_datafields)
        prepare = prepare.replace(prepare.split("def ")[-1].split(":")[0], "_prepare_datafields(self)")
        source += f"class {plot_object.__class__.__name__}({parent}):" + "\n"\
                  + (("    " + "    ".join(prepare.splitlines(True))) if not prepare.startswith("    ") else prepare) \
                  + "\n    "\
                  + "\n    ".join([f"{val[0]} = \"{val[1]}\"" if isinstance(val[1], str) else f"{val[0]} = {val[1]}"
                                   for val in inspect.getmembers(type(plot_object))
                                   if not (str(val[1]).startswith("<") and str(val[1]).endswith(">")) and
                                   not (val[0].startswith("__") and val[0].endswith("__")) and
                                   not val[0] == "_pres_maj" and not val[0] == "_pres_min" and not val[0] == "_" and
                                   not val[0] == "_plot_countries" and not val[0] == "queryable"])
    # All other generic classes
    else:
        source = None

    return source, import_text, import_text_native


def get_plot_details(plot_object, l_type="top", sphinx=False, image_path="", code_path="", dataset=""):
    """
    Returns the .rst or .md file contents containing the plot examples
    """
    layer = "horizontal" if l_type == "Top" else "vertical" if l_type == "Side" else "linear"
    location = DOCS_LOCATION if sphinx else STATIC_LOCATION

    if not os.path.exists(os.path.join(location, "code")):
        os.mkdir(os.path.join(location, "code"))

    if sphinx:
        return get_plot_details_sphinx(plot_object, l_type, layer, dataset, image_path.split("-")[-1].split(".png")[0])

    text = ""
    text += f"![]({image_path})\n\n"
    source, instructions, instructions_native = source_and_import(plot_object, l_type, layer, dataset)
    if instructions:
        text += f"**How to use this plot**  \n" \
                f"Make sure you have the required datafields " \
                f"({', '.join(f'`{field[1]}`' for field in plot_object.required_datafields)})  \n"
        if instructions_native:
            text += "You can use it as is by appending this code into your `mss_wms_settings.py`:  \n"
            text += f"---\n```python\n{instructions_native}\n```" \
                    f"\n---\n"
            if source:
                text += "**If you want to modify the plot**  \n"
        if source:
            text += f"1. [Download this file]({code_path}?download=True)  \n" \
                    f"2. Put this file into your mss_wms_settings.py directory, e.g. `~/mss`  \n" \
                    f"3. Append this code into your `mss_wms_settings.py`:  \n"
            text += f"---\n```python\n{instructions}\n```\n---\n"
            text += f"<details><summary>{l_type}_{dataset}{plot_object.name}.py</summary>\n```python\n" + source + \
                    "\n```\n</details>"
    return text


def get_plot_details_sphinx(plot_object, l_type, layer, dataset="", image_details=None):
    """
    Write .py example files and returns the .rst file content for the sphinx docs
    """
    if not os.path.exists(os.path.join(DOCS_LOCATION, "code", "downloads")):
        os.mkdir(os.path.join(DOCS_LOCATION, "code", "downloads"))

    text = ""
    source, instructions, instructions_native = source_and_import(plot_object, l_type, layer, dataset)
    text += f"{l_type}_{plot_object.name}\n" + "-" * len(f"{l_type}_{plot_object.name}") + "\n"
    text += f".. image:: ../plots/{l_type}_{dataset}{plot_object.name}-{image_details}.png\n\n"
    text += f"""**How to use this plot**

Make sure you have the required datafields ({', '.join(f'`{field[1]}`'for field in plot_object.required_datafields)})

"""
    if instructions_native:
        text += f"""You can use it as is by appending this code into your `mss_wms_settings.py`:

.. code-block:: python

    {"    ".join(instructions_native.splitlines(True))}

{"**If you want to modify the plot**" if source else ""}"""
    if source:
        text += f"""

1. Download this :download:`file <downloads/{l_type}_{dataset}{plot_object.name}.py>`

2. Put this file into your mss_wms_settings.py directory, e.g. `~/mss`

3. Append this code into your `mss_wms_settings.py`:

.. code-block:: python

   {"   ".join(instructions.splitlines(True))}

.. raw:: html

   <details>
   <summary><a>Plot Code</a></summary>

.. literalinclude:: downloads/{l_type}_{dataset}{plot_object.name}.py

.. raw:: html

   </details>
"""
        with open(os.path.join(DOCS_LOCATION, "code", "downloads",
                               f"{l_type}_{dataset}{plot_object.name}.py"), "w+") as py:
            py.write(source)
    return text


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
    plt.close(fig)


def add_image(plot, plot_object, generate_code=False, sphinx=False, url_prefix="", dataset=None, level=None, itime=None,
              vtime=None, simple_naming=False):
    """
    Adds the images to the plots folder and generates the html codes to display them
    """
    global end
    # Import here due to some circular import issue if imported too soon
    from mslib.index import SCRIPT_NAME

    if not os.path.exists(STATIC_LOCATION) and not sphinx:
        os.mkdir(STATIC_LOCATION)

    l_type = "Linear" if isinstance(plot_object, AbstractLinearSectionStyle) else \
        "Side" if isinstance(plot_object, AbstractVerticalSectionStyle) else "Top"

    filename = f"{l_type}_{dataset}{plot_object.name}-" + (
        f"{level}it{itime}vt{vtime}".replace(" ", "_").replace(":", "_").replace("-", "_")
        if not simple_naming else "")

    if plot:
        location = DOCS_LOCATION if sphinx else STATIC_LOCATION
        if not os.path.exists(os.path.join(location, "plots")):
            os.mkdir(os.path.join(location, "plots"))
        if l_type == "Linear":
            create_linear_plot(etree.fromstring(plot), os.path.join(location, "plots", filename + ".png"))
        else:
            with Image.open(io.BytesIO(plot)) as image:
                image.save(os.path.join(location, "plots", filename + ".png"),
                           format="PNG")

    end = end.replace("files = [", f"files = [\"{filename}.png\",")\
        .replace(",];", "];")
    img_path = f"../_static/{filename}.png" if sphinx \
        else f"{url_prefix}/static/plots/{filename}.png"
    code_path = f"code/{l_type}_{dataset}{plot_object.name}.html" if sphinx \
        else f"{url_prefix if url_prefix else ''}{SCRIPT_NAME}mss/code/{l_type}_{dataset}{plot_object.name}.md"

    if generate_code:
        if f"{l_type}_{dataset}{plot_object.name}" not in plot_htmls:
            plot_htmls[f"{l_type}_{dataset}{plot_object.name}"] = \
                plot_html_begin + get_plot_details(plot_object, l_type, sphinx, img_path, code_path, dataset)
        markdown = plot_htmls[f"{l_type}_{dataset}{plot_object.name}"]
        if level:
            markdown = add_levels([level], None, markdown)
        if vtime:
            markdown = add_times(itime, [vtime], markdown)
        plot_htmls[f"{l_type}_{dataset}{plot_object.name}"] = markdown

    id = img_path.split(f"-{level}")[0]
    if not any([id in html for html in plots[l_type]]):
        plots[l_type].append(image_md(
            img_path, plot_object.name, code_path if generate_code else None,
            f"{plot_object.title}" + (f"<br>{plot_object.abstract}"
                                      if plot_object.abstract else "")))


def add_levels(levels, l_type=None, text=None):
    global begin
    replace_begin = not text
    if replace_begin:
        text = begin

    level_select = text.split("name=\"levels\"")[-1].split("</select>")[0]
    if l_type:
        if f"optgroup label=\"{l_type}\"" not in level_select:
            text = text.replace(
                level_select, level_select +
                f"<optgroup label=\"{l_type}\" id=\"{l_type}\"></optgroup>")
        level_select = text.split(f"label=\"{l_type}\"")[-1].split("</optgroup>")[0]
    text = text.replace(level_select, level_select + "".join([
        f"<option value='{level}'>{level}</option>"
        for level in levels if f"value='{level}'" not in level_select]))
    if replace_begin:
        begin = text
    return text


def add_times(itime, vtimes, text=None):
    global begin
    replace_begin = not text
    if replace_begin:
        text = begin

    time_select = text.split("name=\"times\"")[-1].split("</select>")[0]
    if f"optgroup label=\"{itime}\"" not in time_select:
        text = text.replace(time_select, time_select + f"<optgroup label=\"{itime}\" id=\"{itime}\"></optgroup>")
    opt_group = text.split(f"label=\"{itime}\"")[-1].split("</optgroup>")[0]
    text = text.replace(opt_group, opt_group + "".join([
        f"<option value='{time}'>{time}</option>"
        for time in vtimes if f"value='{time}'" not in opt_group]))

    if replace_begin:
        begin = text
    return text
