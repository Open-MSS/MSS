Creating your own Linear-View plot
----------------------------------

Linear-View plots are very simple, and thus simple to create. If you wish to add your own quantity to a Linear-View all you need to do is add the following to your mss_wms_settings.py

.. code-block:: python

   from mslib.mswms import mpl_lsec_styles
   register_linear_layers = [] if not register_linear_layers else register_linear_layers
   register_linear_layers.append((mpl_lsec_styles.LS_DefaultStyle, "air_temperature", "ml", [next(iter(data))]))

Replace "air_temperature" with the quantity you want displayed, and "ml" with the type of file your quantity is present in (ml, pl, al, pv, tl). And you are done!

It will produce a plot akin to this, which the client is able to adjust to its liking

.. image:: ../plots/Linear_LS_AT-.png
