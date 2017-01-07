#!/bin/bash

here=$(dirname $0)

# output image size
width=1024
height=768

# black border width
xborder=120
yborder=100

interior_x1=$xborder
interior_x2=$(( $width - $xborder ))
interior_y1=$yborder
interior_y2=$(( $height - $yborder ))

# remaining space in the center
interior_w=$(( width - xborder * 2 ))
interior_h=$(( height - yborder * 2 ))

# whitespace between the black border and the logos
logoborder=40

# "Powered by Raspbian" dimensions (use "-debug annotate" to find these)
rpitext_w=142
rpitext_h=16
# extra whitespace between the Pi logo and the text
rpitext_hspace=10

# logo dimensions
falogo_w=300
falogo_h=$(( falogo_w * 119 / 288 ))
rpilogo_h=$(( falogo_h - rpitext_h - rpitext_hspace ))
rpilogo_w=$(( rpilogo_h * 570 / 720 ))


# space we have above the logos
topspace=$(( height - yborder * 2 - falogo_h - logoborder ))

# centers of the two main lines of text (Center gravity)
line1_center=$( printf '+0%+d' $(( yborder + interior_h * 25 / 100 - height/2 )) )
line2_center=$( printf '+0%+d' $(( yborder + (interior_h * 25 / 100 + topspace) / 2 - height/2 )) )

# top-left corner of the FA logo (NorthWest gravity)
falogo_x=$(( xborder + logoborder ))
falogo_y=$(( height - yborder - logoborder - falogo_h ))
falogo_geom=$( printf '%dx%d%+d%+d' $falogo_w $falogo_h $falogo_x $falogo_y )

# top-center of the Pi logo (North gravity)
rpilogo_x=$(( width - xborder - logoborder - rpitext_w/2 - width/2 ))
rpilogo_y=$(( height - yborder - logoborder - rpitext_h - rpitext_hspace - rpilogo_h ))
rpilogo_geom=$( printf '%dx%d%+d%+d' $rpilogo_w $rpilogo_h $rpilogo_x $rpilogo_y )

# top-center of the "Powered by Raspbian" text (North gravity)
rpitext_x=$rpilogo_x
rpitext_y=$(( rpilogo_y + rpilogo_h + rpitext_hspace ))
rpitext_pos=$( printf '%+d%+d' $rpitext_x $rpitext_y )

convert-im6 -size 1024x768 -colorspace sRGB \
        'canvas:#000000' \
        -fill '#ffffff' -stroke '#adadad' -strokewidth 2 -draw "rectangle ${interior_x1},${interior_y1} ${interior_x2},${interior_y2}" \
        -font 'Gillius-ADF-Regular----' -style Normal -fill '#002f5d' -stroke none \
        -pointsize 48 -gravity Center -annotate ${line1_center} "PiAware $1 is starting.." \
        -pointsize 26 -gravity Center -annotate ${line2_center} "For more information, visit https://flightaware.com/adsb/piaware/" \
        -pointsize 16 -gravity North  -annotate ${rpitext_pos}  "Powered by Raspbian" \
        -density 150 $here/raspberry-pi-logo.svg   -gravity North -geometry ${rpilogo_geom} -compose SrcOver -composite \
        -density 150 $here/FA_logo_2c_with_tag.eps -gravity NorthWest -geometry ${falogo_geom}  -compose SrcOver -composite \
        "$2"
