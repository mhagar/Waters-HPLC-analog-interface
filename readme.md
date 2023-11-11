# A Digital Chart-Recorder Interface for Use with Old Waters HPLCs

We have an old Waters HPLC setup sitting around: a 515 pump connected to a 2487 dual wavelength detector. It still works great, but it's hooked up to an old [chart-recorder](https://faraday.physics.utoronto.ca/specs/goerz-se120.html). As in, *a device with a rolling drum of paper and electronically controlled pens*. I had a lot of fun using the chart recorder at first, but once the novelty wears off, it's quite cumbersome: so I put together an interface to generate chromatograms on a computer instead.

This program is specifically designed to read from the [ADC-10-F103C](https://github.com/swharden/ADC-10-F103C), an inexpensive 10-channel ADC board with a USB adapter. You can get these for $5-$20 from eBay, Amazon, AliExpress, etc.

## Instructions:

### Setting up the detector

![[Connection_Diagram.svg]]

- Make the connections in the above diagram. For more information, see page 71 of the 2487 detector manual: *'Connecting the 2487 Detector to a Chart Recorder'*
	- *Note: you don't have to connect the red wires to specifically `IN8` and `IN1`, but if you do anything different, make sure to edit the `ACTIVE_CHANNELS` variable at the top of the script.*
- Plug the device into a USB port and run the program

### Usage
- Make sure you have Python 3.10, `matplotlib`, and `tkinter`
- On Linux, the serial port is typically `/dev/ttyUSB0`
	- If you're on Windows, google something about COM ports. I don't have Windows so I can't test it!
- If you get a `Permission denied` error when trying to initialize a connection, try;
```bash
$ sudo chmod o+rw /dev/ttyUSB0
```
- Controls are self explanatory
- By default, the plot scrolls to fit the chromatogram. Hit `Unlock View` to disable this, if you wanted to zoom/pan around. Hit `Lock View` to return to automatic scrolling




