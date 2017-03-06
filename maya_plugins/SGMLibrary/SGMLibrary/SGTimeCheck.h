#pragma once

#include "SGBase.h"
#include <maya/MString.h>
#include <sys/timeb.h> // timeb ����ü�� ����ϱ� ���� �ݵ�� include!!

class SGTimeCheck {
public:
	void start();
	float getInterval();

	void finish(MString frontName);
	struct timeb m_start, m_end;
};