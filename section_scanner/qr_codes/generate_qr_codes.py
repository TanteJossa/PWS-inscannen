import os
import segno

output = './'
try:
    os.makedirs(output)
except:
    pass

for i in range(10):
    qr_code = segno.make(str(i+1))
    qr_code.save(output+str(i+1)+'.png', scale=5, border=0)


# qr = qrcode.QRCode(
#     version=1,
#     error_correction=qrcode.constants.ERROR_CORRECT_L,
#     box_size=3,
#     border=0,
# )
# qr.add_data('1')
# qr.make(fit=True)

# img = qr.make_image(fill_color="black", back_color="white")
# img.show()