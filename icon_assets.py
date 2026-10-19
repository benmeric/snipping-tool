"""
Ekran Alıntısı Aracı - Windows 11 Fluent Yüksek Çözünürlüklü Vektör İkon Üreteci
===================================================================
Windows 11 Snipping Tool (Ekran Alıntısı Aracı) tasarımına birebir uyan,
kenar taşması yapmayan, pürüzsüz 4x supersampled ikonlar sağlar.
"""

import os
import io
import base64
import math
from PIL import Image, ImageDraw, ImageTk, ImageFilter
import customtkinter as ctk

_CTK_CACHE = {}

_GOOGLE_LENS_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAMAAAADACAYAAABS3GwHAAAWP0lEQVR4nO3dC3wU1b0H8N/v7G5I2ISX"
    "PLxtLdRHsYgKJNT6QLMb8P0CChe1rfb2Af3ca1vRXpGAbkuCWj9VS7VV7+3L1orQC1iu4otkC0Wtgtiq"
    "3FqpCh+L8lIku0DYnfO/n1nC85OEPGZ2ZnfO99OWJpk952Qzv50zM2fOIYwOidWllpG4EAVABE81ziq/"
    "yOt2FALldQMKQXV96uZC2fltdlvjdambvG5HIaDXDfC7eN2uswT6jyTCKCAiyAp4ZnJWdLXXbfEzE4B2"
    "nJmQfmWR9DoAg1CIBP9U4egpz83gx143xa9MF6gdZZH07wt257cRn7Sy6fleN8PPTADaEKtLz7T/QYGz"
    "zwidanpXrfDr0wXqI1+P6BXgsXxAWHOB9pWFH9gp/v9oF5ULDu/zT6BV5AlY++Q3l63xW+K5o/slILv9"
    "7fFnA+0ygTgELH69Oxi6Pe3ez5Qn7rB63b4iTkHKNJ+f1vM+cDhivqPHeR+f1vM+cDhiv4PHuh+f1vM"
    "+cABgQ9AvL4pUcz9/vbOB6rrU99BwAX6HKB6TlM1FRsY0PdBgIwCqpbXlv8VARXIP7ztrETTwNII1gE8"
    "BgEmwLuSiZ6aTDCFAApmF0iEPSJYFPSd30ZgCMOp3yKgAhmAeH3qBwTP9rodfkHyilhd07cRQIHrAgW9"
    "398WCej5QKB2AtPvb58E8HwgOF0g0+8/KgbwfMCXR4DY7elKajlVRD4Dqr6A9Caklwh7gRLqWqnsTWCE"
    "020tRl/5ZP36az551z+79GLCArBThDsV9MdCfkTI2yFar7EGr8BnPA9ATX3qNC1yDomYACMInuh1mwzg"
    "vuHVOCn6F8fLFeDvANaCSEaYWck43kDQAhCbm76cWn8JwAUge3nRBqN9x5a8i5+dNgY9Q26fDsgOES5T"
    "Sn8mXGMtQ7EGoGZu0zARfhOCq0AMzFe9RteN6bcEs076av4qFNkE4pFwKPsQY1hfFAGIz2mKC/m9QppX"
    "xzjo34fchMsH/Rx5JaJBPC6ac0vOz6wuyABUz0ldSIW7CAx3qw4jP+4bfh5Oinp0e0BkFYhbImOzKwsi"
    "ANWJ1LEqLPNATnK6bMMbg0o24oHTzs7D+UBbRAT8eaRH5j85Bh/59j5ArC79TRWWN83OX1w27/007n77"
    "Jx62gCTw9eye8JvZZ0NXO1qyE4VUJ6QPw+nHSJzvRHmGP10/5EZcOugXfnisc0EkmrmOZ2G35wGIzd11"
    "BkQvJvAv3S3L8LcQM7jvlBiOj3p66T5HgH9EkLmcY+2hLR51geL1TddT9Itm5w8GSyL4wVsPY5dV7nVT"
    "7E/uE7KIvJFdHprkSQBi9am7Ac7rTuVG4Xm/+Xj8cP2D8AsRPrZ3eWRa3rpAwxJScqw9YMqc6Abat4dM"
    "xyWDfgnfoNwTqclOd/0IMCicXmx2fuP+DXdiw66h8A3hDZnl4btdDUC8LnUPiYs7W4lRnOcDib//Dnus"
    "MviG8IbOdoc6HID4nPQ3QHy3Sw0zitKm5uPxo7fvh59Qy/3ZZ0OXOBqAWH3qAih5qFstM4rSig/H48nN"
    "18I3SCXgAmnAKR3a/GgbnFu367gwrdfsB0ocaaBRdCLcg/uHV2NwzzfhFyJYH9GZEbwA6S4fAewrPmHo"
    "J8zOb7QnI6W+Ox8gcWI2FH70aNu1G4BBkdS9IE51tGVG0Z4P3POOl+OFWsPL9j4bub7dLdr6wbk/SJ0a"
    "DiFQU2QY3Xf9kBt3XzroF/45FECawqHs8YxhW2s/bXPt21AI/wWfEOA9imwUIuN1W4z2/ffGBM/p+7j0"
    "Kdl2AsBPwXOsyFiRO4HM11r9aWvfrK5LXauIX8Eby0SQ1Cr0QlbJhlUzem70qB2GA2Q5BmcRHgyNs0DE"
    "AY7zpB0KVSXxzJoOBSBel9qc/+d25fckbls+s6Jbo/sMf5NnMCKrwnMAXprfiuVPkXHZMUcNgD3CM5+D"
    "3OxPe0tz+opbo2vzVafhvUxD+Gxo3ANwdN4qpZwXqcmuOOxbh35R+aBEem1Lb8jH8GYR7BFiRrK2/Mdu"
    "12X4kyxAKNsvPBOC20CG3K9QlkfGZce2eRm019bUN/Iytl/kLaGMNjt/sHEyrMjY7BwQYwD5wP0KWSPP"
    "YmTb9wGIfCyh+XJzpLwyWVvxeh7qMgpAZGz2hbCVPd1+ysvtujKI3NRqF8h+tNF+usvV2gUbqKKVy2dy"
    "u6v1GAVJGnFi1gq/BLCvi7XsCVvZ/vuHSBw8Aojl7ogmwZashGJm5zfaYs8GJ+AF9k4K17DUUqF/ba0L"
    "NMW9SoGsxtgVs8vecbMOo/CVjM28TJEvulmHgF85LAA19alxdPew8/0Vt5a/5l75RjEJj7OeEMDNdYzH"
    "yNOIHgiAdnGdXBG801BbYa/FaxgdFinJTIfILriBVFYkVHOwCyTiXgAoM90q2yhePBfvA+j0M74dJRZy"
    "+7yqTkg5yS+4UongL8naCjcPZUYRC+vsHfb6AW6ULeR59r8qFEm5diuawJ1ulW0UP9qXKgUPuFI2MFKe"
    "R5nSgs+5UYEA7zfMKj/qEzmG0Z6wZN17yiaFoQpUw9wpnb93p1wjSHg+NgHyvBtlWyp0soKIK7MbUZQJ"
    "gOGU/4ELhByqCJzkeMHA7oZZZYcNOzWMrgozm4QLRPOzSiBRF4p+yfkyjcCKYy0g3V4L4EikDLSPACWO"
    "Fyw0D7cYjiHtTgUcH0kgwv72LFqOB0AgbzldphFsInRj2dRjFIlSx4tV6j3HyzQCjZR3HS8T0s/RRfIO"
    "sFd5NQwHibDVeX26hYy6EgCC7gTLCCxFvdWVct0oFLDanHDLMLpEsBcuMJ/URqCZABiBZgJgBJoJgBFo"
    "JgBGoJkAGIFmLld6wH4MVYf2DGBY91dCRUttS1s9tv45wZ1ety1oTABcVJ2Q/iqcHgd7bWXBKQL0BzCA"
    "TJfin44jN3hcaURVFvH6lP2NTSLYSsjbWqmnlVZPNcwq2+D171KsTACcJMLYHbtGQduLicsllPRosKWb"
    "yQ4sybnPJ0h8AuDpSmQ8aNlT1q+D8Ekt8sSAoeUrF06m5e4vEhwmAA6xJxfT9enbSVQe+KZjI6I4DMQw"
    "Rd607a30u/G61K06G300mWDWqRqCypwEd5M9qXCsrukFAZ45bOd3CYEhIB5WkdQb8bqmSfZRx+06i5kJ"
    "QBfVzG0aFq9LLbVn1HZrXqX28bMgF8Tq0y/F6lO5Wc6MzjMB6ILquempIvwriPyuc9UKElUEnovVp+aa"
    "o0HnmQB0RkJUvK7pZ0rEnqzJ/SV9OoHALbH61OIz7xYfrdHrfyYAHXT2nVIRC6efBjkNPkXyirJd6VVj"
    "6tPuL3NVJEwAOiBet3twSTb1EonDFljzJWJkBLK6uj41wuumFAITgA7czBJYKwmejMLxCQLPmxAcnQlA"
    "O6oTEmYktYTEcSgwBMoo+IMdYK/b4mcmAO1gJHUfwbNRoOzgMpxabAfZ67b4lQlAG+J16WkEp6LAkTzH"
    "DrLX7fArE4BWxOt2nSWUeSgSdpDtQHvdDj8yATjCRfOkB2j9hkAERUQod1cnUsd63Q6/CQvkj46XqsJb"
    "UKCad6a/BfJ4FBn7pBgRsRcrNEeCQ5hb50d8+u/ZmX6XRFF+UoogSwmf3DC79B8oMNlnQ5OF6jGnyzVd"
    "oCM+/Yt157eRCAuzs71uh5+YABzy6S/AzSh+18Tn7DnB60b4hQlAi+ad6RuK+dN/P3MUOJwJQAshrkRA"
    "kHJl5YNSVFe5usoEIDfkIXd58PMIDPau2JI2D9GYAOyjwryy48+sFwelcKHXbfADE4DcxCQ6cDuDiATu"
    "d25N4ANg94UJxBAwJIdWz20upCHergh8AHJ9YbIXAkjpTGBO/NsS+AAoJR7M6OAPAgT+gZnAB0BQ/Nf+"
    "20QJ7u/eIvABgLAPgkoCHP4WJgBEYANABjj8LUwAgv0p2AcBF/hnRYMw/qcdPaoT0ieZ4A74nIBbIM4/"
    "uxL4AIjIDpKDEEAiyA4YhiYUgMi4bNIeteJ0uaYLRHyAgCKxPehrDZgACN9FQIkEN/z7BT4ADPARAEH+"
    "3VsEPgAI8qegBPh3bxH4AGhKYHcCmiOACQBY8ioCSkMC+7vvF/gAJGf2+JuIvImgEezNhMufQMAFPgA2"
    "kksQMEI0rrqZBXEPwE0mAHZXQFTgAkAJXuhbYwJgd4Nm9XwRkI8REAKIzooJgAnAQSJ8CsHxUjJRHvgr"
    "QDYTgP2U+gkCgsJfed0GvzABaNE4s+cqETg++arfCPB6Q7bnQ163wy9MAA4hodAMAEU9OEzI2UhQe90O"
    "v+DWsVWODzEtbbbeqFi5disKUKy+6YFiWBqpVSLPN8yqKNg1z9wQFmGj04XujqjJABaiADVncGuPMK4l"
    "UYoiowW1XrfBb0wX6AjPJyq2kPgxiowATydnV9gPlRiHMAFohc5EEyLyIorHpiz4Va8b4UcmAK1IJrhH"
    "qfJLBbIeBU4gTWLJ+Stro+973RY/MgFow/KZ3E4duVBEtnndlu4886uAKxpvrXjD67b4lQlAO3KLyanQ"
    "pQLsRgES4LrltRWOX+QoJiYAR9E4s+efhbzankMdBUW+n5xV/ojXrfA7E4AOSM6MLhEJDxOgAB6gl+2E"
    "xBtqK+w1gY2jMAHooMbZpW/uyUQrRfAcfMp+sKc5FBpluj0dZwLQCS8k+GFjNnoBRB6A3wj+d2+kfPSq"
    "GT03et2UQmIC0FkJ6oZZFd8SYKw9sMzr5kDwTy24riEbvcI84dV5JgBd1FhbvrwxEz1dgGsFeM+T6/vC"
    "2t09oyclZ5X/2gxw65rAzw3aLQnqRuDhM++WhaW7U7dQeCOInm5f2wfkoaxCYmVttCAHHPqJCYADXphO"
    "+z7BrWffmX4gkpVJFFxM4nwn6xDgzwCfsCQ0f8Xs0recLDvITAActOrm6CYgN5Dux+ffJdFMZvcFEH0J"
    "9gWiU9OwC+Qjgk9D8KTORpclEyzYO9J+ZgLgkme+xzSARS3/RXVC+rPHrsEQDqbWnwYwGJDBAMMANwhl"
    "IyAbwNCGrMjGlbXlRT12Z9iCSeU9dPYEKgkza21Yc/VSTwLOLTWjxfFSRU8e2LCmIJ8HMJw3asHlJ1KH"
    "qyk8T4DTQAwm0PvQbQSyC8KNJNYJsEJDJ9dOWfwXuMwcAQxXDH388oqK3ZGbAXwNuqX7x9x/WkWwJwh7"
    "4e6TCUwIQaFq/sQPBbJIS/a2tVf9we5eOs4EwHDUsAWTSsq0NRW7ORvAgG4W14/g10OMXFP56IR79+rm"
    "u1675omP4CBzH8BwRgJq1GMTv1SmrTcJzmP3d/5DlZG8pUT1+Meo+RO/Z4fMqYLNEcBwxMihX4wpLfeD"
    "7AWXkOxL4PZSS+8CcL8TZZojgNFtVfMnTA1Rngbh2s5/iJAi7quaP+En9lGnu4WZABjdUvnoxGkA7cGB"
    "IeQV/6Pq5Ak/9WcASOcvrRq+M2r+hC8AmOddCzh1XwB9FgAFFt2cOkYr1/YFS0lE4K15VY9NONtXARBB"
    "mRvlGv6hdOQBkv29bocdQNF4pKtXhhREdjjdKC3Sx+kyDf+omj9+CoAa+ATJwT0ta2ZXXquA3JgVZymc"
    "6HiZhi8Msz9phT+Ezwgxo3LBJHuMVacoQBx/iojAZ50u0/CHMq2ngzwOPkOwBy2r08FUAji+NJAIz3C6"
    "TMMfCFwHnxJy/Bm/vaiT9yIUwQ1ON4RE2dZ45SinyzW8Vfm7ifZgtaHwKQIlVrj04s68Rgnhyhq5AnSq"
    "IUYBULgSfifsVBuVgjsBADrXEKMAiP8DIOSFlQ9WdvjehIK2/uZKS8jKbdWV9iHTKBaUEfC53IM2FUNO"
    "6Oj2qn/pzteRm2nAeVop+4EIowgM+WV1qX2lBQVAVMfvQykuW98MyCpXWkJ8eXv1GZ9ypWwjr/qU9unU"
    "Q/2e0p0IgP0/Ari1dE7ICln1LpVt5JGiKpwAkMd2KgBKuRYAO11f3l7z+TNdK9/IC630HhShXAAGPLc6"
    "CYE780qStEQWbD/jjHw8LGG4JILIBygUIh90ejSoAPNdaxDxKSuqf+ta+YbrogO2bhNBBgVAh7sQAGr9"
    "sGstmtWAy7bGq25ztQ7DNclYMkvIhyiyo9WBAAxMrvmTQN52+SZFYku80lwaLVBCvAqfE5FNL09e2PkA"
    "tHgQbqO6Y0u8qs71egznCZfA50gs7cz2hwWA1q6fQuDoxEOtImu31FT93PV6DEdZsJ6Cz2ktS7ocgIHJ"
    "dSkS9yIv+G+b41WvbY+NPiU/9Rnd9epVS+xFAl0aO9Z9Auxl08bl3XomOGxl5rl2SfQIJIdbCq9vqan6"
    "9UfVI4bko06je0Q69wmbX9K4ZuqaTLcC0Df56g4Ibkde8SuZUOSdzfHRyzfHK6dtO3fU5/Jbv9FRYWv3"
    "XAB+vCdg6QimdvZFbU3Wi801o98m8JluN6uLRGQrwD+B+jXIvnmG7Oc3c3MOafuhMy328EQINWgf/bRI"
    "y8+UstfL0gJNsX+W+75ondve/jr3Oi2K1Pb2++Yxanm9XV6uHi3S8vp92+l92+1/vf06JVrsf3PlWhIi"
    "7dfofdtZufpz2ypq0VbL6ymh3GzgWotSOncTssCMmj/huwq8B74iD66esmiaY3ODKi3fFcXH4RGS9uSq"
    "4wE1fn9M5fABHC0bHvwmD6Sk5f8cenzjwS9y21Ht2+7At1spr+Vb+7Y74mCZ+5KHFBvat5T8IV8fWj/V"
    "wYnTctsxF4PDaiwUO3vt/lmfj8uuB3k8/ECwxwqF7NmonZsXaEDj6j8A8P1Zv5F/6y9e1qyJawDYa6N5"
    "j3rq2skLtzo+MVZZqPlaEWzucsOMovXKlEUvaugvid0Z9JLI91dPWdzlUQztBqDimb9uCWvrSrcemDEK"
    "2ytTFi8Syo1e1S+CX6++alGiO2UcdWrEY5KvvEhiRncqMYrXK1MW3QvINPsafH5rlh+uCamvdbeUDp+A"
    "bY6PfoTE1d2t0DjcwOUvF9xJcGtGLhh/ZsjiUpDHwEW5oIl8dc1Vi37nRHkdnhx3oI5eC5E/OlGpUXzW"
    "Tl78glWCShH8zc2Bblrpaqd2/k4FgMlkls1NlwHyf05VbhSXtRMXbSgJqVGg3CwiTo4p2y0id+7VzcPto"
    "DlhbuevQW8/d/RxVlieBenbGcIKSbF0gY506iOX9O0RKr1RRL5BciC6QARpUB51c5nULr35O845te/e"
    "HqXP2DNlO9+kYCnWAByQgKocNv4s6NxEaVcSbHfOHhHZAmKpQJbsUeFn1k1e6OrJdZfffLnoxB5bm/ss"
    "BnmRs00KlqIPwBEql17WE3sjvdHM3vb8PfZ4EIYyOzRKPs4AH6+bvDCFPOrWmy+A2hYbXSsKt+V/kbTi"
    "ELQA+E23lkgioAc0vjxHtJxn7hgbhciRNcIGNa5eVab1cAgWOVGeYeSLY4vk9Uqu2Taw4eWJ0HIJBO85"
    "Va5huMnxVSIHNq5+Ejr9OW/XjzWMjnH1BGxL9ehjofAdUL4FsLebdRUqcxLsrby8+Vuqh5UzFJ0qyD2y"
    "dlI+6iwUJgDeyvubv7V6ZJUwdJ0oXkWgHwLOBMBbnr35Mgmh7R+OHiXQYzQ4BoJz/LDyeL6ZAHjLV2/+"
    "R/GRgzMIDQN4uhDDCXxaBP1AqaCgF8iiW4HeBACe+n94YK0ByKEN8wAAAABJRU5ErkJggg=="
)


def _draw_rect_shape(d, cx, cy, S, fg, w):
    d.rounded_rectangle([cx - 8*S, cy - 7*S, cx + 5*S, cy + 5*S], radius=2.5*S, outline=fg, width=w)
    d.rectangle([cx + 1*S, cy + 1*S, cx + 9*S, cy + 9*S], fill=(0, 0, 0, 0))
    px, py = cx + 5*S, cy + 5*S
    pw = 3.2*S
    d.line([(px - pw, py), (px + pw, py)], fill=fg, width=w)
    d.line([(px, py - pw), (px, py + pw)], fill=fg, width=w)


def _draw_window_shape(d, cx, cy, S, fg, w):
    d.rounded_rectangle([cx - 8*S, cy - 7*S, cx + 5*S, cy + 5*S], radius=2.5*S, outline=fg, width=w)
    d.line([(cx - 8*S, cy - 3*S), (cx + 5*S, cy - 3*S)], fill=fg, width=int(1.3*S))
    d.rectangle([cx + 1*S, cy + 1*S, cx + 9*S, cy + 9*S], fill=(0, 0, 0, 0))
    px, py = cx + 5*S, cy + 5*S
    pw = 3.2*S
    d.line([(px - pw, py), (px + pw, py)], fill=fg, width=w)
    d.line([(px, py - pw), (px, py + pw)], fill=fg, width=w)


def _draw_fullscreen_shape(d, cx, cy, S, fg, w):
    L = 4.5*S
    x1, y1, x2, y2 = cx - 7.5*S, cy - 6.5*S, cx + 5.5*S, cy + 5.5*S
    d.line([(x1, y1 + L), (x1, y1), (x1 + L, y1)], fill=fg, width=w)
    d.line([(x2 - L, y1), (x2, y1), (x2, y1 + L)], fill=fg, width=w)
    d.line([(x1, y2 - L), (x1, y2), (x1 + L, y2)], fill=fg, width=w)
    d.line([(x2 - L, y2), (x2, y2), (x2, y2 - L)], fill=fg, width=w)


def _draw_freeform_shape(d, cx, cy, S, fg, w):
    pts = []
    cx1, cy1, r1 = cx - 3*S, cy - 2*S, 4.2*S
    for a in range(120, 280, 10):
        rad = math.radians(a)
        pts.append((cx1 + r1*math.cos(rad), cy1 + r1*math.sin(rad)))
    cx2, cy2, r2 = cx + 2*S, cy - 3*S, 3.8*S
    for a in range(260, 420, 10):
        rad = math.radians(a)
        pts.append((cx2 + r2*math.cos(rad), cy2 + r2*math.sin(rad)))
    cx3, cy3, r3 = cx + 1*S, cy + 2*S, 3.2*S
    for a in range(0, 90, 10):
        rad = math.radians(a)
        pts.append((cx3 + r3*math.cos(rad), cy3 + r3*math.sin(rad)))
    cx4, cy4, r4 = cx - 3*S, cy + 2*S, 3.6*S
    for a in range(90, 140, 10):
        rad = math.radians(a)
        pts.append((cx4 + r4*math.cos(rad), cy4 + r4*math.sin(rad)))
    pts.append(pts[0])
    d.line(pts, fill=fg, width=w, joint="curve")
    d.rectangle([cx + 1*S, cy + 1*S, cx + 9*S, cy + 9*S], fill=(0, 0, 0, 0))
    px, py = cx + 5*S, cy + 5*S
    pw = 3.2*S
    d.line([(px - pw, py), (px + pw, py)], fill=fg, width=w)
    d.line([(px, py - pw), (px, py + pw)], fill=fg, width=w)


def _draw_delay_slash_shape(d, cx, cy, S, fg, w):
    r = 6.2*S
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=fg, width=w)
    d.line([(cx, cy - r - 2.5*S), (cx, cy - r)], fill=fg, width=w)
    d.line([(cx - 2*S, cy - r - 2.5*S), (cx + 2*S, cy - r - 2.5*S)], fill=fg, width=w)
    d.line([(cx, cy), (cx, cy - 3.8*S)], fill=fg, width=w)
    d.line([(cx - 7*S, cy + 6.5*S), (cx + 7*S, cy - 6.5*S)], fill=fg, width=int(1.6*S))


def _draw_delay_timer_shape(d, cx, cy, S, fg, w):
    r = 6.2*S
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=fg, width=w)
    d.line([(cx, cy - r - 2.5*S), (cx, cy - r)], fill=fg, width=w)
    d.line([(cx - 2*S, cy - r - 2.5*S), (cx + 2*S, cy - r - 2.5*S)], fill=fg, width=w)
    d.line([(cx, cy), (cx, cy - 3.8*S)], fill=fg, width=w)
    d.line([(cx, cy), (cx + 3.2*S, cy)], fill=fg, width=w)


# =============================================================================
# 1. SEGMENTED KAMERA / VİDEO İKONLARI (ALT MAVİ ÇUBUKLU)
# =============================================================================
def get_seg_icon(seg_type: str, active: bool = False) -> ctk.CTkImage:
    key = ("seg", seg_type, active)
    if key in _CTK_CACHE:
        return _CTK_CACHE[key]

    S = 4
    W = 36 * S
    H = 30 * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fg = (245, 245, 245, 255) if active else (185, 185, 185, 255)
    cx, cy = 18*S, 12*S
    w = int(1.6*S)

    if seg_type == "camera":
        d.rounded_rectangle([cx - 8.5*S, cy - 5*S, cx + 8.5*S, cy + 7*S], radius=2.5*S, outline=fg, width=w)
        d.polygon([(cx - 4*S, cy - 5*S), (cx - 2.5*S, cy - 7.5*S), (cx + 2.5*S, cy - 7.5*S), (cx + 4*S, cy - 5*S)], outline=fg)
        d.line([(cx - 2.5*S, cy - 7.5*S), (cx + 2.5*S, cy - 7.5*S)], fill=fg, width=w)
        d.ellipse([cx - 3.8*S, cy - 2.5*S, cx + 3.8*S, cy + 4.5*S], outline=fg, width=w)
    else:  # video
        d.rounded_rectangle([cx - 8.5*S, cy - 6*S, cx + 3.5*S, cy + 6*S], radius=2.2*S, outline=fg, width=w)
        d.polygon([(cx + 4*S, cy - 2.5*S), (cx + 8.5*S, cy - 6*S), (cx + 8.5*S, cy + 6*S), (cx + 4*S, cy + 2.5*S)], outline=fg)
        d.line([(cx + 4*S, cy - 2.5*S), (cx + 8.5*S, cy - 6*S)], fill=fg, width=w)
        d.line([(cx + 8.5*S, cy - 6*S), (cx + 8.5*S, cy + 6*S)], fill=fg, width=w)
        d.line([(cx + 8.5*S, cy + 6*S), (cx + 4*S, cy + 2.5*S)], fill=fg, width=w)

    if active:
        # Screenshot 1'deki alt mavi Fluent gösterge çubuğu
        d.rounded_rectangle([cx - 7*S, 24*S, cx + 7*S, 26.5*S], radius=1.5*S, fill=(96, 205, 255, 255))

    res = im.resize((36, 30), Image.Resampling.LANCZOS)
    ctk_img = ctk.CTkImage(light_image=res, dark_image=res, size=(36, 30))
    _CTK_CACHE[key] = ctk_img
    return ctk_img


get_tab_icon = get_seg_icon


# =============================================================================
# 2. ARAÇ ÇUBUĞU İKON + AŞAĞI OK BİRLEŞİK İKONLARI (SCREENSHOT 1)
# =============================================================================
def get_combo_icon(mode_name: str) -> ctk.CTkImage:
    """Kırpma modu ikonu ile yanındaki aşağı oku tek pürüzsüz görselde birleştirir."""
    key = ("combo_mode", mode_name)
    if key in _CTK_CACHE:
        return _CTK_CACHE[key]

    S = 4
    W = 34 * S
    H = 24 * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fg = (245, 245, 245, 255)
    cx, cy = 11*S, 12*S
    w = int(1.6*S)

    if mode_name == "rect":
        _draw_rect_shape(d, cx, cy, S, fg, w)
    elif mode_name == "window":
        _draw_window_shape(d, cx, cy, S, fg, w)
    elif mode_name == "fullscreen":
        _draw_fullscreen_shape(d, cx, cy, S, fg, w)
    elif mode_name == "freeform":
        _draw_freeform_shape(d, cx, cy, S, fg, w)

    # Aşağı Ok (Chevron)
    cw = int(1.5*S)
    d.line([(24*S, 10*S), (27.5*S, 13.5*S), (31*S, 10*S)], fill=(190, 190, 190, 255), width=cw)

    res = im.resize((34, 24), Image.Resampling.LANCZOS)
    ctk_img = ctk.CTkImage(light_image=res, dark_image=res, size=(34, 24))
    _CTK_CACHE[key] = ctk_img
    return ctk_img


def get_delay_combo_icon(delay_sec: int) -> ctk.CTkImage:
    """Zamanlayıcı ikonu ile aşağı oku tek pürüzsüz görselde birleştirir."""
    key = ("combo_delay", delay_sec)
    if key in _CTK_CACHE:
        return _CTK_CACHE[key]

    S = 4
    W = 34 * S
    H = 24 * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fg = (245, 245, 245, 255)
    cx, cy = 11*S, 12.5*S
    w = int(1.6*S)

    if delay_sec == 0:
        _draw_delay_slash_shape(d, cx, cy, S, fg, w)
    else:
        _draw_delay_timer_shape(d, cx, cy, S, fg, w)

    cw = int(1.5*S)
    d.line([(24*S, 10*S), (27.5*S, 13.5*S), (31*S, 10*S)], fill=(190, 190, 190, 255), width=cw)

    res = im.resize((34, 24), Image.Resampling.LANCZOS)
    ctk_img = ctk.CTkImage(light_image=res, dark_image=res, size=(34, 24))
    _CTK_CACHE[key] = ctk_img
    return ctk_img


# =============================================================================
# 3. AÇILIR MENÜ İKONLARI (SCREENSHOT 2 BİREBİR SOL MAVİ ÇUBUKLU)
# =============================================================================
def get_menu_icon(mode_name: str, active: bool = False) -> ctk.CTkImage:
    """Açılır menü satırı için solunda dikey mavi çizgi içeren veya hizalı ikon döndürür."""
    key = ("menu", mode_name, active)
    if key in _CTK_CACHE:
        return _CTK_CACHE[key]

    S = 4
    W = 34 * S
    H = 26 * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fg = (245, 245, 245, 255)

    if active:
        # Screenshot 2'deki sol dikey mavi Fluent çizgisi
        d.rounded_rectangle([1.5*S, 4*S, 4.5*S, 22*S], radius=1.5*S, fill=(96, 205, 255, 255))

    cx, cy = 19*S, 13*S
    w = int(1.6*S)

    if mode_name == "rect":
        _draw_rect_shape(d, cx, cy, S, fg, w)
    elif mode_name == "window":
        _draw_window_shape(d, cx, cy, S, fg, w)
    elif mode_name == "fullscreen":
        _draw_fullscreen_shape(d, cx, cy, S, fg, w)
    elif mode_name == "freeform":
        _draw_freeform_shape(d, cx, cy, S, fg, w)

    res = im.resize((34, 26), Image.Resampling.LANCZOS)
    ctk_img = ctk.CTkImage(light_image=res, dark_image=res, size=(34, 26))
    _CTK_CACHE[key] = ctk_img
    return ctk_img


def get_delay_menu_icon(sec: int, active: bool = False) -> ctk.CTkImage:
    key = ("menu_delay", sec, active)
    if key in _CTK_CACHE:
        return _CTK_CACHE[key]

    S = 4
    W = 34 * S
    H = 26 * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fg = (245, 245, 245, 255)

    if active:
        d.rounded_rectangle([1.5*S, 4*S, 4.5*S, 22*S], radius=1.5*S, fill=(96, 205, 255, 255))

    cx, cy = 19*S, 13*S
    w = int(1.6*S)

    if sec == 0:
        _draw_delay_slash_shape(d, cx, cy, S, fg, w)
    else:
        _draw_delay_timer_shape(d, cx, cy, S, fg, w)

    res = im.resize((34, 26), Image.Resampling.LANCZOS)
    ctk_img = ctk.CTkImage(light_image=res, dark_image=res, size=(34, 26))
    _CTK_CACHE[key] = ctk_img
    return ctk_img


# =============================================================================
# 4. TEKİL İKONLAR (OCR, GOOGLE LENS, KALEM, VURGULAYICI, SİLGİ VB.)
# =============================================================================
def get_icon_ctk(name: str, size: tuple[int, int] = (22, 22)) -> ctk.CTkImage:
    key = ("single", name, size[0], size[1])
    if key in _CTK_CACHE:
        return _CTK_CACHE[key]

    if name == "google_lens":
        lens_img = None
        asset_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "google_lens.png")
        if os.path.exists(asset_file):
            try:
                lens_img = Image.open(asset_file).convert("RGBA")
            except Exception:
                pass
        if lens_img is None:
            try:
                lens_bytes = base64.b64decode(_GOOGLE_LENS_B64)
                lens_img = Image.open(io.BytesIO(lens_bytes)).convert("RGBA")
            except Exception:
                pass
        if lens_img:
            res = lens_img.resize(size, Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=res, dark_image=res, size=size)
            _CTK_CACHE[key] = ctk_img
            return ctk_img

    S = 4
    W = 28 * S
    H = 28 * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fg = (245, 245, 245, 255)
    cx, cy = 14*S, 14*S
    w = int(1.6*S)

    if name == "rect":
        rw = 8.5 * S
        rh = 6.5 * S
        d.rounded_rectangle([cx - rw, cy - rh, cx + rw, cy + rh], radius=2*S, outline=fg, width=w)

    elif name == "window":
        rw = 8.5 * S
        rh = 6.5 * S
        d.rounded_rectangle([cx - rw, cy - rh, cx + rw, cy + rh], radius=2*S, outline=fg, width=w)
        d.line([(cx - rw, cy - 2.5*S), (cx + rw, cy - 2.5*S)], fill=fg, width=w)
        d.line([(cx - rw + 2.5*S, cy - 4.5*S), (cx - rw + 3.5*S, cy - 4.5*S)], fill=fg, width=w)

    elif name == "fullscreen":
        mw = 8.5 * S
        d.rounded_rectangle([cx - mw, cy - 7*S, cx + mw, cy + 3*S], radius=2*S, outline=fg, width=w)
        d.line([(cx, cy + 3*S), (cx, cy + 7*S)], fill=fg, width=w)
        d.line([(cx - 4.5*S, cy + 7*S), (cx + 4.5*S, cy + 7*S)], fill=fg, width=w)

    elif name == "freeform":
        pts = []
        cx1, cy1, r1 = cx - 3.5*S, cy - 2.5*S, 4.5*S
        for a in range(120, 280, 10):
            rad = math.radians(a)
            pts.append((cx1 + r1*math.cos(rad), cy1 + r1*math.sin(rad)))
        cx2, cy2, r2 = cx + 2.5*S, cy - 3.5*S, 4.0*S
        for a in range(260, 420, 10):
            rad = math.radians(a)
            pts.append((cx2 + r2*math.cos(rad), cy2 + r2*math.sin(rad)))
        cx3, cy3, r3 = cx + 2.0*S, cy + 2.5*S, 4.0*S
        for a in range(0, 90, 10):
            rad = math.radians(a)
            pts.append((cx3 + r3*math.cos(rad), cy3 + r3*math.sin(rad)))
        cx4, cy4, r4 = cx - 3.5*S, cy + 2.5*S, 4.2*S
        for a in range(90, 140, 10):
            rad = math.radians(a)
            pts.append((cx4 + r4*math.cos(rad), cy4 + r4*math.sin(rad)))
        pts.append(pts[0])
        d.line(pts, fill=fg, width=w, joint="curve")

    elif name == "ocr":
        # Screenshot 1'deki OCR / Tarayıcı simgesi
        x1, y1, x2, y2 = 4*S, 5*S, 24*S, 23*S
        c_len = 4*S
        d.line([(x1, y1 + c_len), (x1, y1), (x1 + c_len, y1)], fill=fg, width=w)
        d.line([(x2 - c_len, y1), (x2, y1), (x2, y1 + c_len)], fill=fg, width=w)
        d.line([(x1, y2 - c_len), (x1, y2), (x1 + c_len, y2)], fill=fg, width=w)
        d.line([(x2 - c_len, y2), (x2, y2), (x2, y2 - c_len)], fill=fg, width=w)
        d.line([(8*S, 11*S), (20*S, 11*S)], fill=fg, width=w)
        d.line([(8*S, 16*S), (18*S, 16*S)], fill=fg, width=w)

    elif name == "dots":
        # Üç nokta (...)
        r = 1.6*S
        d.ellipse([7*S - r, cy - r, 7*S + r, cy + r], fill=fg)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fg)
        d.ellipse([21*S - r, cy - r, 21*S + r, cy + r], fill=fg)

    elif name == "pen":
        d.line([(19*S, 5*S), (23*S, 9*S)], fill=fg, width=w)
        d.line([(23*S, 9*S), (10*S, 22*S)], fill=fg, width=w)
        d.line([(10*S, 22*S), (5*S, 23*S)], fill=fg, width=w)
        d.line([(5*S, 23*S), (6*S, 18*S)], fill=fg, width=w)
        d.line([(6*S, 18*S), (19*S, 5*S)], fill=fg, width=w)
        d.line([(9*S, 19*S), (19*S, 9*S)], fill=fg, width=w)

    elif name == "highlighter":
        hl = (255, 235, 59, 255)
        d.line([(19*S, 5*S), (23*S, 9*S)], fill=hl, width=w)
        d.line([(23*S, 9*S), (13*S, 19*S)], fill=hl, width=w)
        d.line([(13*S, 19*S), (9*S, 15*S)], fill=hl, width=w)
        d.line([(9*S, 15*S), (19*S, 5*S)], fill=hl, width=w)
        d.polygon([(9*S, 15*S), (13*S, 19*S), (7*S, 23*S), (5*S, 21*S)], fill=hl)

    elif name == "eraser":
        d.line([(13*S, 6*S), (22*S, 15*S)], fill=fg, width=w)
        d.line([(22*S, 15*S), (15*S, 22*S)], fill=fg, width=w)
        d.line([(15*S, 22*S), (6*S, 13*S)], fill=fg, width=w)
        d.line([(6*S, 13*S), (13*S, 6*S)], fill=fg, width=w)
        d.line([(10*S, 9*S), (18*S, 17*S)], fill=fg, width=w)

    elif name == "undo":
        d.arc([7*S, 7*S, 21*S, 21*S], 200, 380, fill=fg, width=w)
        d.polygon([(5*S, 14*S), (10*S, 10*S), (10*S, 18*S)], fill=fg)

    elif name == "copy":
        d.rounded_rectangle([9*S, 5*S, 22*S, 18*S], radius=2*S, outline=fg, width=w)
        d.rectangle([5*S, 9*S, 18*S, 22*S], fill=(0, 0, 0, 0))
        d.rounded_rectangle([6*S, 9*S, 19*S, 23*S], radius=2*S, outline=fg, width=w)

    elif name == "save":
        d.rounded_rectangle([5*S, 5*S, 23*S, 23*S], radius=2*S, outline=fg, width=w)
        d.rectangle([8*S, 5*S, 20*S, 11*S], outline=fg, width=w)
        d.rectangle([8*S, 15*S, 20*S, 23*S], outline=fg, width=w)

    elif name == "arrow_left":
        d.line([(18*S, 6*S), (8*S, 14*S), (18*S, 22*S)], fill=fg, width=int(1.8*S))
        d.line([(8*S, 14*S), (23*S, 14*S)], fill=fg, width=int(1.8*S))

    elif name == "mic":
        d.rounded_rectangle([11*S, 5*S, 17*S, 15*S], radius=3*S, outline=fg, width=w)
        d.arc([8*S, 10*S, 20*S, 18*S], 0, 180, fill=fg, width=w)
        d.line([(14*S, 18*S), (14*S, 23*S)], fill=fg, width=w)
        d.line([(10*S, 23*S), (18*S, 23*S)], fill=fg, width=w)

    elif name == "mic_off":
        d.rounded_rectangle([11*S, 5*S, 17*S, 15*S], radius=3*S, outline=(150, 150, 150, 255), width=w)
        d.arc([8*S, 10*S, 20*S, 18*S], 0, 180, fill=(150, 150, 150, 255), width=w)
        d.line([(14*S, 18*S), (14*S, 23*S)], fill=(150, 150, 150, 255), width=w)
        d.line([(10*S, 23*S), (18*S, 23*S)], fill=(150, 150, 150, 255), width=w)
        d.line([(7*S, 7*S), (21*S, 21*S)], fill=(232, 17, 35, 255), width=int(2*S))

    elif name == "speaker":
        d.line([(6*S, 11*S), (10*S, 11*S), (15*S, 7*S), (15*S, 21*S), (10*S, 17*S), (6*S, 17*S), (6*S, 11*S)], fill=fg, width=w)
        d.arc([14*S, 10*S, 20*S, 18*S], -60, 60, fill=fg, width=w)
        d.arc([16*S, 7*S, 24*S, 21*S], -60, 60, fill=fg, width=w)

    elif name == "speaker_off":
        d.line([(6*S, 11*S), (10*S, 11*S), (15*S, 7*S), (15*S, 21*S), (10*S, 17*S), (6*S, 17*S), (6*S, 11*S)], fill=(150, 150, 150, 255), width=w)
        d.line([(7*S, 7*S), (21*S, 21*S)], fill=(232, 17, 35, 255), width=int(2*S))

    elif name == "combine":
        d.rounded_rectangle([cx - 8.5*S, cy - 8*S, cx - 1*S, cy + 8*S], radius=1.5*S, outline=fg, width=w)
        d.rounded_rectangle([cx + 1*S, cy - 8*S, cx + 8.5*S, cy - 1*S], radius=1.5*S, outline=fg, width=w)
        d.rounded_rectangle([cx + 1*S, cy + 1*S, cx + 8.5*S, cy + 8*S], radius=1.5*S, outline=fg, width=w)

    elif name == "plus":
        d.line([(cx - 6*S, cy), (cx + 6*S, cy)], fill=fg, width=w)
        d.line([(cx, cy - 6*S), (cx, cy + 6*S)], fill=fg, width=w)

    elif name == "trash":
        d.line([(cx - 6*S, cy - 6*S), (cx + 6*S, cy - 6*S)], fill=fg, width=w)
        d.line([(cx - 2.5*S, cy - 8*S), (cx + 2.5*S, cy - 8*S)], fill=fg, width=w)
        d.line([(cx - 5*S, cy - 5*S), (cx - 4*S, cy + 7*S), (cx + 4*S, cy + 7*S), (cx + 5*S, cy - 5*S)], fill=fg, width=w)
        d.line([(cx - 1.8*S, cy - 3*S), (cx - 1.8*S, cy + 5*S)], fill=fg, width=int(1.2*S))
        d.line([(cx + 1.8*S, cy - 3*S), (cx + 1.8*S, cy + 5*S)], fill=fg, width=int(1.2*S))

    elif name == "up":
        d.line([(cx - 5*S, cy + 2*S), (cx, cy - 4*S), (cx + 5*S, cy + 2*S)], fill=fg, width=int(1.8*S))

    elif name == "down":
        d.line([(cx - 5*S, cy - 2*S), (cx, cy + 4*S), (cx + 5*S, cy - 2*S)], fill=fg, width=int(1.8*S))

    elif name == "grid":
        d.rounded_rectangle([cx - 7.5*S, cy - 7.5*S, cx - 1*S, cy - 1*S], radius=1*S, outline=fg, width=w)
        d.rounded_rectangle([cx + 1*S, cy - 7.5*S, cx + 7.5*S, cy - 1*S], radius=1*S, outline=fg, width=w)
        d.rounded_rectangle([cx - 7.5*S, cy + 1*S, cx - 1*S, cy + 7.5*S], radius=1*S, outline=fg, width=w)
        d.rounded_rectangle([cx + 1*S, cy + 1*S, cx + 7.5*S, cy + 7.5*S], radius=1*S, outline=fg, width=w)

    elif name == "vertical":
        d.rounded_rectangle([cx - 7*S, cy - 8*S, cx + 7*S, cy - 1*S], radius=1.5*S, outline=fg, width=w)
        d.rounded_rectangle([cx - 7*S, cy + 1*S, cx + 7*S, cy + 8*S], radius=1.5*S, outline=fg, width=w)

    elif name == "horizontal":
        d.rounded_rectangle([cx - 8*S, cy - 7*S, cx - 1*S, cy + 7*S], radius=1.5*S, outline=fg, width=w)
        d.rounded_rectangle([cx + 1*S, cy - 7*S, cx + 8*S, cy + 7*S], radius=1.5*S, outline=fg, width=w)

    elif name == "windows":
        w_tile = 5.2 * S
        gap = 1.2 * S
        d.rounded_rectangle([cx - gap - w_tile, cy - gap - w_tile, cx - gap, cy - gap], radius=1*S, fill=fg)
        d.rounded_rectangle([cx + gap, cy - gap - w_tile, cx + gap + w_tile, cy - gap], radius=1*S, fill=fg)
        d.rounded_rectangle([cx - gap - w_tile, cy + gap, cx - gap, cy + gap + w_tile], radius=1*S, fill=fg)
        d.rounded_rectangle([cx + gap, cy + gap, cx + gap + w_tile, cy + gap + w_tile], radius=1*S, fill=fg)


    res = im.resize(size, Image.Resampling.LANCZOS)
    ctk_img = ctk.CTkImage(light_image=res, dark_image=res, size=size)
    _CTK_CACHE[key] = ctk_img
    return ctk_img


def create_app_icon_image(size=256) -> Image.Image:
    """Windows 11 Snipping Tool koyu zemin ve makaslı orijinal uygulama ikonunu üretir."""
    # Pürüzsüz kenarlar için 4x supersampling ile çizilip hedeflenen boyuta indirilir
    supersample = 4
    canvas_size = size * supersample
    S = canvas_size / 32.0

    im = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # 1. Koyu arka plan ve açık mavi/camgöbeği kenarlık
    d.rounded_rectangle(
        [6*S, 4*S, 28*S, 26*S],
        radius=5*S,
        fill=(38, 38, 38, 255),
        outline=(96, 205, 255, 255),
        width=max(1, int(2.2*S))
    )
    # 2. Kırmızı makas sapı halkası
    d.ellipse(
        [4*S, 18*S, 13*S, 27*S],
        outline=(255, 90, 95, 255),
        width=max(1, int(2.2*S))
    )
    # 3. Mavi makas sapı halkası
    d.ellipse(
        [12*S, 20*S, 21*S, 29*S],
        outline=(96, 205, 255, 255),
        width=max(1, int(2.2*S))
    )
    # 4. Makas bıçakları
    d.line(
        [(9*S, 20*S), (24*S, 7*S)],
        fill=(235, 235, 235, 255),
        width=max(1, int(2.2*S))
    )
    d.line(
        [(16*S, 21*S), (9*S, 10*S)],
        fill=(235, 235, 235, 255),
        width=max(1, int(2.2*S))
    )
    # 5. Makas vidası (beyaz nokta)
    d.ellipse(
        [12*S, 15*S, 14*S, 17*S],
        fill=(255, 255, 255, 255)
    )

    return im.resize((size, size), Image.Resampling.LANCZOS)


_APP_ICON_B64 = (
    "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"
    "+b98AAAAAElFTkSuQmCC"
)


def get_app_icon_image() -> Image.Image:
    """Ekran Alıntısı Aracı uygulama simgesini döndürür."""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    png_path = os.path.join(app_dir, "assets", "app_icon.png")
    if os.path.exists(png_path):
        try:
            return Image.open(png_path).convert("RGBA")
        except Exception:
            pass
    try:
        raw = base64.b64decode(_APP_ICON_B64)
        return Image.open(io.BytesIO(raw)).convert("RGBA")
    except Exception:
        pass
    return create_app_icon_image(256)


def ensure_app_icon_ico() -> str:
    """Tüm standart boyutları (16, 20, 24, 32, 48, 64, 72, 96, 256) içeren app_icon.ico dosyasını üretir ve yolunu döndürür."""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    ico_path = os.path.join(app_dir, "app_icon.ico")
    png_path = os.path.join(app_dir, "assets", "app_icon.png")

    needs_rebuild = not os.path.exists(ico_path) or os.path.getsize(ico_path) < 1000
    if not needs_rebuild and os.path.exists(png_path):
        if os.path.getmtime(png_path) > os.path.getmtime(ico_path):
            needs_rebuild = True

    if needs_rebuild:
        base_img = get_app_icon_image()
        sizes = [(16, 16), (20, 20), (24, 24), (32, 32), (48, 48), (64, 64), (72, 72), (96, 96), (256, 256)]
        base_img.save(ico_path, format="ICO", sizes=sizes)
    return ico_path



def setup_windows_app_id():
    """Windows görev çubuğunda python.exe yerine programın kendi ikonunun görünmesini sağlar."""
    if os.name == "nt":
        try:
            import ctypes
            myappid = "meric.ekranalintisi.snippingtool.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass


def apply_window_icon(window):
    """Pencereye hem Windows görev çubuğu hem de başlık çubuğu için özel ikonu bağlar."""
    try:
        ico_path = ensure_app_icon_ico()
        if os.path.exists(ico_path):
            window.iconbitmap(ico_path)
    except Exception:
        pass

    try:
        photo = get_app_icon_photo((32, 32))
        window.iconphoto(True, photo)
    except Exception:
        pass


def get_app_icon_photo(size=(32, 32)) -> ImageTk.PhotoImage:
    """Pencere başlığı ve görev çubuğu için yüksek çözünürlüklü PhotoImage döndürür."""
    ensure_app_icon_ico()
    base_img = get_app_icon_image()
    resized = base_img.resize(size, Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(resized)
