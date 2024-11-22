from rmqrcode import rMQR
import rmqrcode

data = "https://oudon.xyz"
qr = rMQR.fit(
    data,
    fit_strategy=rmqrcode.FitStrategy.MINIMIZE_WIDTH
)