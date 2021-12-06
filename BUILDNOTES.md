# Build Notes
Connect all the parts before soldering anything in place. They will not function without properly secured connections, but checking how they fit together can save you from time-consuming mistakes. You'll need a soldering iron, solder and preferably also cutting pliers, a metal file and some flux to complete the build. Below you find some tips on how to fit the parts together as neatly as possible.

## Build Process
The depicted device did not have pre-soldered header pins, allowing me to shorten the pins on the underside rather than the top. Leaving the ends connecting to the display unaltered. Depending on your model you may therefore need to make some changes to the below steps.
- Push the header pins through from the underside, leaving 4.5 mm of the pins exposed on the top (pre-soldered headers extend 9 mm above the board for comparison).
- Layer the buttonSHIM on the top directly against the RPI0w.
- Solder the headers on the top to the buttonSHIM using plenty of flux. Leaving as much of the pins clean as possible so they still fit into the display's socket.
- Cut and remove the black plastic separator from the headers on the underside, leaving only bare pins on this side of the board as well.
- Solder the pins to the underside of the board, ensuring a good electrical connection to the RPI0w.
- Cut and file down the pins on the underside to make room for the UPS-Lite. Shortening them enough so they don't poke or scratch the battery.
- Secure the UPS-Lite using the included hexagonal nuts. The screws are just barely long enough to accommodate the thickness of both the RPI0w and buttonSHIM.
- Carefully press down the eINK module on the male pin headers without applying excessive force to the display itself.

## GPIO Header
Whether your RPI0w comes with pre-soldered male header or not, I recommend removing the black spacer. This way you can position the buttonSHIM directly against the board on the top with only the female header of the eINK display module and the buttonSHIM itself adding to the overall height of the device. 

## Waveshare Display:
- In order to fit the screen onto the device as snugly as possible, make sure to desolder or by other means detach the large white connector. The yellow kapton tape didn't end up being needed since the covered components don't make contact with the RPI0w.

![waveshare_stock](https://user-images.githubusercontent.com/17461433/144749374-befd978c-a6eb-4e9a-a1fc-603ed09b6914.jpg)
![waveshare_modified](https://user-images.githubusercontent.com/17461433/112752795-6a5dab00-8fdd-11eb-8e15-bd59c9444a42.jpeg)

## ButtonSHIM:
- Take care to orient the module correctly.
- Soldering it into place you want to aim for small but secure solder joints. Any extra solder on the pins will limit how close to the board you can fit the screen. An X-Acto knife or small file can help with potentially needed clean-up.

![buttonshim_attached](https://user-images.githubusercontent.com/17461433/112752878-cc1e1500-8fdd-11eb-98e5-62af52a660a2.jpeg)

## UPS-Lite:
- Make sure the pins on the bottom don't extend too far before screwing the module onto the board. They should not be allowed to touch the battery pack. I ended up filing the pins down quite a bit to ensure sufficient clearance. Shape and length of the pins is important for the pogo pins to make good contact.
- In the picture you can also spot a couple of the pins on the top and just how low the solder joints need to be for connecting the display.

![upslite_attached](https://user-images.githubusercontent.com/17461433/112752928-1acbaf00-8fde-11eb-8281-5b35784cc348.JPG)

## Real Time Clock
- If you want to add a RTC module to keep the device synced while powered off, I recommend the [DS3231](https://www.pishop.us/product/ds3231-real-time-clock-module-for-raspberry-pi/). A good [setup guide](https://learn.adafruit.com/adding-a-real-time-clock-to-raspberry-pi/set-rtc-time) has been published by Adafruit.
- Removing the female headers, the module fits neatly inside the UPS-Lite. You can see the correct wiring and positioning in the below picture. Don't forget to isolate it with some tape and form neat solder joints for the pins shared by the UPS-Lite.

![ds3231_attached](https://user-images.githubusercontent.com/17461433/111912767-cff8e700-8a73-11eb-9bd0-a406bd7241ef.jpg)