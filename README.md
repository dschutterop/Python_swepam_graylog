Python_swepam_graylog
This Python script is a blatant and crude ripoff of Lennart's SpaceWeather plugin (https://marketplace.graylog.org/addons/8adb2876-bdd6-4163-8a39-f218086f6cde).

Since I could only use the http proxy from my environment, I didn't get his Graylog plugin working, so I wrote a Python script to get the swepam data into Graylog by pulling it from the NOA textfile and pushing it through a GELF input on my Graylog cluster.

Props to Lennart Koopmann^^
