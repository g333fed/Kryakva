
// native/windows_helper.cpp
// Пример "C++ момента": отправка хоткеев WinAPI (Win+D) из маленького хелпера.
#include <windows.h>
#include <vector>

void keyDown(WORD vk){ INPUT i={}; i.type=INPUT_KEYBOARD; i.ki.wVk=vk; SendInput(1,&i,sizeof(INPUT)); }
void keyUp(WORD vk){ INPUT i={}; i.type=INPUT_KEYBOARD; i.ki.wVk=vk; i.ki.dwFlags=KEYEVENTF_KEYUP; SendInput(1,&i,sizeof(INPUT)); }
void combo(const std::vector<WORD>& vks){ for(auto vk:vks) keyDown(vk); for(int k=(int)vks.size()-1;k>=0;--k) keyUp(vks[k]); }

int main(){ combo({VK_LWIN,'D'}); return 0; }
