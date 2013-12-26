#include <iostream>
#include <string>

#include "boost/regex.hpp"

void test_regex(void) {
  std::string text(" 192.168.0.1 abc 10.0.0.255 10.5.1 1.2.3.4a 5.4.3.2 ");
  const char* pattern =
      "\\b(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
      "\\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
      "\\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
      "\\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\b";
  boost::regex ip_regex(pattern);

  boost::sregex_iterator it(text.begin(), text.end(), ip_regex);
  boost::sregex_iterator end;
  for (; it != end; ++it) {
      std::cout << it->str() << "\n";
      // v.push_back(it->str()); or something similar
  }
}

int main(void) {
  test_regex();
  return 0;
}