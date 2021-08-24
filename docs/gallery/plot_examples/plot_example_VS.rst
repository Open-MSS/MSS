Creating your own Side-View plot
--------------------------------

Sometimes the classes provided by MSS are not enough. This page will show you how our plot classes are structured and how to build your own one.
This is an example of a Side-View plot class

.. literalinclude:: VS_template.py

It produces the following plot, filled with a temperature colourmap and contour lines

.. image:: ../plots/Side_VSTemplate-None.png

----

By cutting the code into segments it will be easier to understand what it does and how to change it to your liking.

.. literalinclude:: VS_template.py
   :start-after: import mslib.mswms.mpl_vsec_styles
   :end-before: required_datafields

We begin our plots with various identifiers and information which should be self-explanatory.

----

.. literalinclude:: VS_template.py
   :start-after: abstract
   :end-before: def

Within the **required_datafields** you list all quantities your plot initially needs as a list of 3-tuples containing

1. The type of vertical level (ml, pl, al, pv, tl, sfc)
2. The CF standard name of the entity required
3. The desired unit of the entity

To create a VS plot, you require air_pressure to be present. Do not remove it.

----

.. literalinclude:: VS_template.py
   :start-after: ]
   :end-before: # main plot

First inside the plotting function the desired range of the temperature is set. This will be the range of your colourmap.
In this case the colourmap ranges between -93 and 28 °C in steps of 2. Adjust it to your liking.
Second it is decided which entity will fill out the plot and which will just be a contour above it. Of course you don't need both, any one will suffice.
In this case, temperature is both the plot filler and the contour.

----

.. literalinclude:: VS_template.py
   :start-after: contour_entity
   :end-before: # contour

Now the colourmap is decided, in this case "plasma". It is best to pick one which best describes your data.
Here is a `list of all available ones <https://matplotlib.org/stable/tutorials/colors/colormaps.html>`_.
The rest of the code you normally don't have to touch, but feel free to if you like.
Afterwards the plot is filled with the fill_entity and a corresponding colour bar is created.
Of course if you only want a contour plot, you can delete this part of the code.

----

.. literalinclude:: VS_template.py
   :start-after: add_colorbar

Lastly the contour_entity is drawn on top of the plot, in white. Feel free to use any other colour.
Of course if you don't want a contour, you can delete this part of the code.
The final part you don't usually need to touch.

----

That's about it. Feel free to :download:`download this template <VS_template.py>`
and play around with it however you like.

If you wish to include this into your WMS server

1. Put the file into your mss_wms_settings.py directory, e.g. **~/mss**
2. Assuming you didn't change the file or class name, append the following lines into your mss_wms_settings.py

.. code-block:: python

   from VS_template import VS_Template
   register_vertical_layers = [] if not register_vertical_layers else register_vertical_layers
   register_vertical_layers.append((VS_Template, [next(iter(data))]))
