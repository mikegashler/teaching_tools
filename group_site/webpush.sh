#!/usr/bin/expect
set timeout 10

# (No, that is not really my password)
set password 1234

puts ""
puts ""
puts ""
puts "-----------------------"
puts "|  root folder        |"
puts "-----------------------"
spawn rsync --quiet --update --progress --stats --compress \
--rsh=/usr/bin/ssh --recursive --times --perms --links \
--exclude "*~" \
--exclude "*.o" \
--exclude "*.class" \
--exclude "*.tmp" \
--exclude "tmp*" \
--exclude "*.bbl" \
--exclude "*.blg" \
--exclude "*.aux" \
--exclude "*.swp" \
--exclude "*.kate-swp" \
--exclude ".~lock*" \
--exclude "*.lock" \
/home/mike/rs/web/ mgashler@turing.uark.edu:public_html
expect "mgashler@turing.uark.edu's password: "
send "$password\n"
interact

puts ""
puts ""
puts ""
puts "----------------------------"
puts "|  paradigms folder        |"
puts "----------------------------"
spawn rsync --quiet --update --progress --stats --compress \
--rsh=/usr/bin/ssh --recursive --times --perms --links --delete \
--exclude "*~" \
--exclude "*.o" \
--exclude "*.class" \
--exclude "*.tmp" \
--exclude "tmp*" \
--exclude "*.bbl" \
--exclude "*.blg" \
--exclude "*.aux" \
--exclude "*.swp" \
--exclude "*.kate-swp" \
--exclude ".~lock*" \
--exclude "*.lock" \
/home/mike/rs/paradigms/web/ mgashler@turing.uark.edu:public_html/paradigms
expect "mgashler@turing.uark.edu's password: "
send "$password\n"
interact

puts ""
puts ""
puts ""
puts "---------------------"
puts "|  ai folder        |"
puts "---------------------"
spawn rsync --quiet --update --progress --stats --compress \
--rsh=/usr/bin/ssh --recursive --times --perms --links --delete \
--exclude "*~" \
--exclude "*.o" \
--exclude "*.class" \
--exclude "*.tmp" \
--exclude "tmp*" \
--exclude "*.bbl" \
--exclude "*.blg" \
--exclude "*.aux" \
--exclude "*.swp" \
--exclude "*.kate-swp" \
--exclude ".~lock*" \
--exclude "*.lock" \
/home/mike/rs/ai/web/ mgashler@turing.uark.edu:public_html/ai
expect "mgashler@turing.uark.edu's password: "
send "$password\n"
interact

puts ""
puts ""
puts ""
puts "----------------------"
puts "|  lab folder        |"
puts "----------------------"
spawn rsync --quiet --update --progress --stats --compress \
--rsh=/usr/bin/ssh --recursive --times --perms --links --delete \
--exclude "*~" \
--exclude "*.o" \
--exclude "*.class" \
--exclude "*.tmp" \
--exclude "tmp*" \
--exclude "*.bbl" \
--exclude "*.blg" \
--exclude "*.aux" \
--exclude "*.swp" \
--exclude "*.kate-swp" \
--exclude ".~lock*" \
--exclude "*.lock" \
/home/mike/rs/lab/web/ mgashler@turing.uark.edu:public_html/lab
expect "mgashler@turing.uark.edu's password: "
send "$password\n"
interact

puts ""
puts ""
puts ""
puts "--------------------------"
puts "|  waffles folder        |"
puts "--------------------------"
spawn rsync --quiet --update --progress --stats --compress \
--rsh=/usr/bin/ssh --recursive --times --perms --links --delete \
--exclude "*~" \
--exclude "*.o" \
--exclude "*.class" \
--exclude "*.tmp" \
--exclude "tmp*" \
--exclude "*.bbl" \
--exclude "*.blg" \
--exclude "*.aux" \
--exclude "*.swp" \
--exclude "*.kate-swp" \
--exclude ".~lock*" \
--exclude "*.lock" \
/home/mike/waffles/web/ mgashler@turing.uark.edu:public_html/waffles
expect "mgashler@turing.uark.edu's password: "
send "$password\n"
interact

