export default {
	async fetch(request, env, ctx) {
		const url = new URL(request.url);
		const path = url.pathname;
		const IMAGE_HOST = 'https://i2.chuimg.com/';
		let img_prefix = '/proxy-image/';
		if (path.startsWith(img_prefix)) {
			const imagePath = path.slice(img_prefix.length);
			const imageUrl = IMAGE_HOST + imagePath;
			const imageRequest = new Request(imageUrl, {
				method: request.method,
				headers: {
					'Referer': IMAGE_HOST,
					'User-Agent': request.headers.get('User-Agent') || 'Mozilla/5.0',
				},
			});

			const response = await fetch(imageRequest);
			if (response.ok) {
				const contentType = response.headers.get('content-type') || 'image/jpeg';
				return new Response(response.body, {
					status: response.status,
					headers: {
						'Content-Type': contentType,
						'Cache-Control': 'public, max-age=31536000',
						'Access-Control-Allow-Origin': '*',
					},
				});
			} else {
				return new Response('Image not found', { status: response.status });
			}
		}

		return new Response('Not Found', { status: 404 });
	},
};
