int read_unsigned_int(const char* str, size_t size)
{
	if (!str || size == 0)
		return -1;

	int ret = 0;
	while (size > 0)
	{
		if (*str < '0' || *str > '9')
			return -1;

		ret = ret * 10 + (*str - '0');
		str++;
		size--;
	}

	return ret;
}
