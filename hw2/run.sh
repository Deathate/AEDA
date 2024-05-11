iconv -f $(file -bi test_utf8.txt | cut -d '=' -f 2) -t UTF-8 test_utf8.txt -o tmp.txt
g++ -o test.out 'joy_v3.cpp'
./test.out
rm test.out