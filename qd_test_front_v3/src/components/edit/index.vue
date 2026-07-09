<template>
	<div>
		<el-upload
			:action="uploadUrl"
			:before-upload="handleBeforeUpload"
			:on-success="handleUploadSuccess"
			:on-error="handleUploadError"
			name="file"
			:accept="accept"
			:show-file-list="false"
			:headers="headers"
			style="display: none"
			ref="upload"
			v-if="this.type == 'url'"></el-upload>
		<el-upload
			class="avatar-uploader-editor-video"
			:action="uploadUrl"
			name="file"
			ref="videoUpload"
			:headers="headers"
			:show-file-list="false"
			:limit="1"
			:file-list="fileList"
			accept=".mp4"
			style="display: none"
			:on-success="uploadSuccessVideo"
			:on-progress="uploadProgress"
			:before-upload="(file) => handleBeforeUpload(file, 'video')"
			:on-error="handleUploadError"></el-upload>
		<el-upload
			class="avatar-uploader-editor-voice"
			:action="uploadUrl"
			name="file"
			ref="audioUpload"
			:headers="headers"
			:file-list="fileList"
			:show-file-list="false"
			:limit="1"
			accept=".mp3, .ogg, .wav, .flac"
			style="display: none"
			:on-success="uploadSuccessVoice"
			:on-progress="uploadProgress"
			:before-upload="(file) => handleBeforeUpload(file, 'audio')"
			:on-error="handleUploadError"></el-upload>

		<div class="editor" :class="disabled ? 'editor1' : ''" ref="editor" :style="styles"></div>
    <input type="file" v-show="false" ref="uploadImage" @change="uploadAvatar" />

	</div>
</template>

<script>
import Quill from 'quill';
import 'quill/dist/quill.core.css';
import 'quill/dist/quill.snow.css';
import 'quill/dist/quill.bubble.css';
import AudioA from './audio';
import Video from './video';
Quill.register(Video, true);
Quill.register(AudioA, true);

import { getToken } from '@/utils/auth';
// 引用字号和字体css
import './quillEditor.css';
import {swfUploadApi, uploadAvatarApi} from "@/api/user";
// 设置字体大小
const fontSizeStyle = Quill.import('attributors/style/size'); // 引入这个后会把样式写在style上
fontSizeStyle.whitelist = ['16px', '18px', '20px', '26px', '28px', '30px', '34px', '36px'];
Quill.register(fontSizeStyle, true);
// 设置文字水平方式
var Align = Quill.import('attributors/style/align');
Align.whitelist = ['right', 'center', 'justify'];
Quill.register(Align, true);
// const toolbarOptions = [
// 	['bold', 'italic', 'underline', 'strike'], // 加粗 斜体 下划线 删除线
// 	[{ align: [] }], // 对齐方式-----[{ align: [] }]
// 	[{ size: fontSizeStyle.whitelist }], // 字体大小-----[{ size: ['small', false, 'large', 'huge'] }]
// 	[{ header: [1, 2, 3, 4, 5, 6, false] }], // 标题
// 	[{ indent: '-1' }, { indent: '+1' }], // 缩进-----[{ indent: '-1' }, { indent: '+1' }]
// 	['clean'], // 清除文本格式-----['clean']
// 	['link', 'image', 'video', 'audio'], // 链接、图片、视频、音频-----['link', 'image', 'video', 'audio]
// ];

// [
//   ['blockquote', 'code-block'], // 引用  代码块
//   [{ list: 'ordered' }, { list: 'bullet' }], // 有序、无序列表
//   [{ indent: '-1' }, { indent: '+1' }], // 缩进
//   [{ size: ['small', false, 'large', 'huge'] }], // 字体大小
//   [{ header: [1, 2, 3, 4, 5, 6, false] }], // 标题
//   [{ color: [] }, { background: [] }], // 字体颜色、字体背景颜色
//   [{ align: [] }], // 对齐方式
//   ['clean'], // 清除文本格式
//   ['link', 'image'] // 链接、图片、视频
// ]
export default {
	name: 'Editor',
	props: {
		toolbarOptions: {
			type: Array,
			default() {
				return [
					['bold', 'italic', 'underline', 'strike'], // 加粗 斜体 下划线 删除线
					[{ align: [] }], // 对齐方式-----[{ align: [] }]
					[{ size: fontSizeStyle.whitelist }], // 字体大小-----[{ size: ['small', false, 'large', 'huge'] }]
					[{ header: [1, 2, 3, 4, 5, 6, false] }], // 标题
					[{ indent: '-1' }, { indent: '+1' }], // 缩进-----[{ indent: '-1' }, { indent: '+1' }]
					['clean'], // 清除文本格式-----['clean']
					// ['link', 'image', 'video', 'audio'], // 链接、图片、视频、音频-----['link', 'image', 'video', 'audio]
					['link', 'image'], // 链接、图片-----['link', 'image']
				];
			},
		},
		/* 编辑器的内容 */
		value: {
			type: String,
			default: '',
		},
		/* 高度 */
		height: {
			type: Number|String,
			default: null,
		},
		/* 最小高度 */
		minHeight: {
			type: Number,
			default: null,
		},
		/* 只读 */
		readOnly: {
			type: Boolean,
			default: false,
		},
		/* 禁用 */
		disabled: {
			type: Boolean,
			default: false,
		},
		/* 音频 */
		audioShow: {
			type: Boolean,
			default: false,
		},
		/* 视频 */
		videoShow: {
			type: Boolean,
			default: false,
		},
		/* 工具栏显隐 */
		toolbarShow: {
			type: Boolean,
			default: true,
		},
		// 上传文件大小限制(MB)
		fileSize: {
			type: Number,
			default: 5,
		},
		// 上传音视频文件大小限制(MB)
		noImgFileSize: {
			type: Number,
			default: 100,
		},
		/* 类型（base64格式、url格式） */
		type: {
			type: String,
			default: 'url',
		},
		accept: {
			type: String,
			default: '.jpg,.jpeg,.png',
		},
		placeholder: {
			// 默认提示词
			type: String,
			default: '请输入内容',
		},
	},
	data() {
		return {
			uploadUrl: process.env.VUE_APP_BASE_API + '/seller/swf_upload.ajax', // 上传的图片服务器地址
			headers: {
				token: getToken(),
			},
			Quill: null,
			currentValue: '',
			options: {
				theme: 'snow',
				bounds: document.body,
				debug: 'warn',
				modules: {
					// 工具栏配置
					toolbar: this.toolbarShow ? this.toolbarOptions : false,
				},
				placeholder: this.placeholder,
				readOnly: this.readOnly,
			},
			progressLoading: '',
			fileList: [],
		};
	},
	computed: {
		styles() {
			let style = {};
			if (this.minHeight) {
				style.minHeight = `${this.minHeight}px`;
			}
			if (this.height) {
				style.height = `${this.height}px`;
			}
			return style;
		},
	},
	watch: {
		value: {
			handler(val) {
				if (val !== this.currentValue) {
					this.currentValue = val === null ? '' : val;
					// console.log(val);
					if (this.Quill) {
						// this.Quill.pasteHTML(this.currentValue);
						this.$refs.editor.children[0].innerHTML = this.currentValue;
						if (this.readOnly) {
							this.Quill.enable(true);
							setTimeout(() => {
								this.Quill.enable(false);
							}, 600);
						}
					}
				}
			},
			immediate: true,
		},
	},
	mounted() {
		this.init();
	},
	beforeDestroy() {
		this.Quill = null;
	},
	methods: {
    uploadAvatar() {
      const file = this.$refs["uploadImage"].files[0],
        type = file.type,
        size = file.size;
      if (type !== "image/jpeg" && type !== "image/png") {
        this.$refs["uploadImage"].value = "";
        return this.$notify.warning({
          title: "提示",
          message: "只能上传PNG和JPG格式",
        });
      }
      if (size / 1000 > 2048) {
        this.$refs["uploadImage"].value = "";
        return this.$notify.warning({
          title: "提示",
          message: "头像大小不能超过2M",
        });
      }
      uploadAvatarApi(file).then(res => {
        console.log(res)
        this.handleUploadSuccess(res)
      })


    },
		init() {
      let _this = this;
			const editor = this.$refs.editor;
			this.Quill = new Quill(editor, this.options);
			if (!this.readOnly) {
				this.Quill.enable(false); //解决富文本自动聚焦
				// setTimeout(() => {
				this.Quill.enable(true); //一秒之后可点击
				// }, 1000);
			} else {
				this.Quill.enable(true);
				setTimeout(() => {
					this.Quill.enable(false);
				}, 600);
			}
			// 如果设置了上传地址则自定义图片上传事件
			let toolbar = this.Quill.getModule('toolbar');
			// console.log(this.$refs.upload, '111', this.$refs.videoUpload);
			if (this.toolbarShow && this.type == 'url' && !this.readOnly) {
				toolbar.addHandler('image', (value) => {
          _this.$refs.uploadImage.click()
					// this.uploadType = 'image';
					// if (value) {
					// 	this.$refs.upload.$children[0].$refs.input.click();
					// } else {
					// 	this.quill.format('image', false);
					// }
				});
				toolbar.addHandler('video', (value) => {
					this.uploadType = 'video';
					if (value) {
						// document.querySelector('.avatar-uploader-editor-video input').click();
						this.$refs.videoUpload.$children[0].$refs.input.click(); //
					} else {
						this.quill.format('video', false);
					}
				});
				toolbar.addHandler('audio', (value) => {
					this.uploadType = 'audio';
					if (value) {
						// document.querySelector('.avatar-uploader-editor-voice input').click();
						this.$refs.audioUpload.$children[0].$refs.input.click();
					} else {
						this.quill.format('audio', false);
					}
				});
			}
			// this.Quill.pasteHTML(this.currentValue);
			this.$refs.editor.children[0].innerHTML = this.currentValue;
			this.Quill.on('text-change', (delta, oldDelta, source) => {
				const html = this.$refs.editor.children[0].innerHTML;
				const text = this.Quill.getText();
				const quill = this.Quill;
				this.currentValue = html;
				this.$emit('input', html);
				this.$emit('on-change', { html, text, quill });
			});
			this.Quill.on('text-change', (delta, oldDelta, source) => {
				this.$emit('on-text-change', delta, oldDelta, source);
			});
			this.Quill.on('selection-change', (range, oldRange, source) => {
				this.$emit('on-selection-change', range, oldRange, source);
			});
			this.Quill.on('editor-change', (eventName, ...args) => {
				this.$emit('on-editor-change', eventName, ...args);
			});
		},
		//获取时长的函数
		getTimes(file) {
			var video = document.createElement('video');
			video.preload = 'metadata';

			return new Promise((resolve, reject) => {
				video.onloadedmetadata = function () {
					var url = video.src;
					if (url.startsWith('blob:')) {
						url = url.substr(5);
					}
					window.URL.revokeObjectURL(url);
					var duration = video.duration;
					resolve(parseInt(duration));
					console.log('视频长度为：' + duration);
				};
				video.src = URL.createObjectURL(file);
			});
			// console.log(file)
			// let url = URL.createObjectURL(new Blob([file]));
			// console.log(new Audio(url))
			// let audioElement = new Audio(url);
			//
			// return new Promise((resolve, reject) => {
			// 	audioElement.addEventListener('loadedmetadata', function () {
			//     console.log('6666')
			//
			// 		resolve(parseInt(audioElement.duration));
			// 	});
			// });
		},
		// 上传前校检格式和大小
		handleBeforeUpload(file, type) {
			return new Promise((resolve, reject) => {
				console.log(file, type);
				// 校检文件大小
				const fileSize = this.videoShow ? this.noImgFileSize : this.audioShow ? this.noImgFileSize : this.fileSize;
				if (fileSize) {
					const isLt = file.size / 1024 / 1024 < fileSize;
					if (!isLt) {
						this.$message.error(`上传文件大小不能超过 ${fileSize} MB!`);
						return reject(false);
					}
				}
				if ((this.audioShow && type == 'audio') || (this.videoShow && type == 'video')) {
					if (this.videoShow && type == 'video') {
						if (this.value && this.value.match(/<audio/g) && this.value.match(/<audio/g).length) {
							this.$message.error(`只能上传一个视频或者一个音频!`);
							return reject(false);
						}
						let pointIndex = file.name.lastIndexOf('.');
						let fileType = file.name.substring(pointIndex + 1); //获取到文件后缀名
						if (fileType !== 'mp4') {
							this.$message.error('你选择的文件不是视频哦，仅支持mp4格式');
							return reject(false);
						}
						if (this.value && this.value.match(/\.mp4/g) && this.value.match(/\.mp4/g).length) {
							this.$message.error(`只能上传一个视频!`);
							return reject(false);
						}
					}
					if (this.audioShow && type == 'audio') {
						if (this.value && this.value.match(/\.mp4/g) && this.value.match(/\.mp4/g).length) {
							this.$message.error(`只能上传一个视频或者一个音频!`);
							return reject(false);
						}
						// file.type好像只能返回图片的格式，其他的将会是 ""， 所以需要自己获取后缀名判断文件格式
						let pointIndex = file.name.lastIndexOf('.');
						let fileType = file.name.substring(pointIndex + 1); //获取到文件后缀名
						// if (fileType !== 'mp3' && fileType !== 'ogg' && fileType !== 'wav') {
						if (fileType !== 'mp3' && fileType !== 'ogg' && fileType !== 'flac' && fileType !== 'wav') {
							this.$message.error('你选择的文件不是音频哦，仅支持mp3、ogg、flac、wav格式');
							return reject(false);
						}
						if (this.value && this.value.match(/<audio/g) && this.value.match(/<audio/g).length) {
							this.$message.error(`只能上传一个音频!`);
							return reject(false);
						}
					}
					// 限制音频小于等于60s
					this.getTimes(file).then((res) => {
						console.log(res);
						let length = this.Quill.getSelection().index;
						// 调整光标到最后
						this.Quill.setSelection(length + 1);
						if (this.audioShow && type == 'audio') {
							if (res > 100) {
								this.$message.error('上传音频时长不能超过 60S');
								return reject(false);
							}
						}
						if (this.videoShow && type == 'video') {
							if (res > 60) {
								this.$message.error('上传视频时长不能超过 60S');
								return reject(false);
							}
						}
						return resolve(true);
					});
				} else {
					return resolve(true);
				}
			});
		},
		handleUploadSuccess(res, file) {
			let quill = this.Quill;
			const url =
				res?.obj?.url || res?.url || res?.data?.url;
			const ok = res?.res === true || res?.code === 0 || !!url;
			if (ok && url) {
				let length = quill.getSelection().index;
				quill.insertEmbed(length, 'image', url);
				quill.setSelection(length + 1);
			} else {
				this.$message.error(res?.resMsg || res?.message || '图片上传失败');
			}
		},
		//上传视频
		uploadSuccessVideo(res, file) {
			// 获取富文本组件实例
			let quill = this.Quill;
			// 如果上传成功
			if (res.code == 200) {
				// 获取光标所在位置
				let length = quill.getSelection().index;
				// let length = 0;
				// 插入视频res.url为服务器返回的地址
				if (window.location.protocol == 'https:') {
					res.data.url = res.data.url.replace('http:', 'https:');
				}
				console.log(res.data.url, 'res.data.url');
				quill.insertEmbed(length, 'video', res.data.url);
				// 调整光标到最后
				quill.setSelection(length + 1);
				this.$emit('videoSuccess', { type: 'video', val: res });
				this.progressLoading.close();
				this.$refs.videoUpload.clearFiles();
			} else {
				this.$refs.videoUpload.clearFiles();
				this.fileList = [];
				this.$message.error('视频插入失败');
				this.progressLoading.close();
			}
		},
		//上传音频-处理很重要！！！！
		uploadSuccessVoice(res, file) {
			// 获取富文本组件实例
			let quill = this.Quill;
			// 如果上传成功
			if (res.code == 200) {
				// 获取光标所在位置
				let length = quill.getSelection().index;
				// let length = 0;
				let BlockEmbed = Quill.import('blots/block/embed');
				class AudioBlot extends BlockEmbed {
					static create(value) {
						let node = super.create();
						node.setAttribute('src', res.data.url); //设置audio的src属性
						node.setAttribute('controls', true); //设置audio的controls，否则他将不会显示
						node.setAttribute('controlsList', 'nodownload'); //设置audio的下载功能为不能下载
						node.setAttribute('id', 'voice'); //设置一个id
						return node;
					}
				}
				AudioBlot.blotName = 'audio';
				AudioBlot.tagName = 'audio'; //自定义的标签为audio
				Quill.register(AudioBlot);

				// insertEmbed(index: Number(插入的位置), type: String(标签类型), value: any(参数，将传入到create的方法中去), source: String = 'api')
				quill.insertEmbed(length, 'audio', res.data.url);
				quill.setSelection(length + 1); //光标位置向后移动一位
				this.progressLoading.close();
				this.$emit('videoSuccess', { type: 'audio', val: res });
				this.$refs.audioUpload.clearFiles();
			} else {
				this.$refs.audioUpload.clearFiles();
				this.fileList = [];
				this.$message.error('音频插入失败');
				this.progressLoading.close();
			}
		},
		uploadProgress() {
			console.log('jinru');
			this.progressLoading = this.$loading({
				lock: true,
				text: '上传中...',
				spinner: 'el-icon-loading',
				background: 'rgba(0, 0, 0, 0.4)',
			});
		},
		handleUploadError() {
			this.fileList = [];
			this.$message.error('插入失败');
		},
	},
};
</script>

<style>
.editor,
.ql-toolbar {
	white-space: pre-wrap !important;
	line-height: normal !important;
}
.quill-img {
	display: none;
}
.ql-snow .ql-tooltip[data-mode='link']::before {
	content: '请输入链接地址:';
}
.ql-snow .ql-tooltip.ql-editing a.ql-action::after {
	border-right: 0px;
	content: '保存';
	padding-right: 0px;
}

.ql-snow .ql-tooltip[data-mode='video']::before {
	content: '请输入视频地址:';
}

.ql-snow button.ql-audio {
	background-image: url('./audio.svg');
	background-size: 18px 18px;
	background-repeat: no-repeat;
	background-position: center;
}

.ql-snow .ql-picker.ql-size .ql-picker-label::before,
.ql-snow .ql-picker.ql-size .ql-picker-item::before {
	content: '14px';
}
.ql-snow .ql-picker.ql-size .ql-picker-label[data-value='small']::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value='small']::before {
	content: '10px';
}
.ql-snow .ql-picker.ql-size .ql-picker-label[data-value='large']::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value='large']::before {
	content: '18px';
}
.ql-snow .ql-picker.ql-size .ql-picker-label[data-value='huge']::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value='huge']::before {
	content: '32px';
}

.ql-snow .ql-picker.ql-header .ql-picker-label::before,
.ql-snow .ql-picker.ql-header .ql-picker-item::before {
	content: '文本';
}
.ql-snow .ql-picker.ql-header .ql-picker-label[data-value='1']::before,
.ql-snow .ql-picker.ql-header .ql-picker-item[data-value='1']::before {
	content: '标题1';
}
.ql-snow .ql-picker.ql-header .ql-picker-label[data-value='2']::before,
.ql-snow .ql-picker.ql-header .ql-picker-item[data-value='2']::before {
	content: '标题2';
}
.ql-snow .ql-picker.ql-header .ql-picker-label[data-value='3']::before,
.ql-snow .ql-picker.ql-header .ql-picker-item[data-value='3']::before {
	content: '标题3';
}
.ql-snow .ql-picker.ql-header .ql-picker-label[data-value='4']::before,
.ql-snow .ql-picker.ql-header .ql-picker-item[data-value='4']::before {
	content: '标题4';
}
.ql-snow .ql-picker.ql-header .ql-picker-label[data-value='5']::before,
.ql-snow .ql-picker.ql-header .ql-picker-item[data-value='5']::before {
	content: '标题5';
}
.ql-snow .ql-picker.ql-header .ql-picker-label[data-value='6']::before,
.ql-snow .ql-picker.ql-header .ql-picker-item[data-value='6']::before {
	content: '标题6';
}

.ql-snow .ql-picker.ql-font .ql-picker-label::before,
.ql-snow .ql-picker.ql-font .ql-picker-item::before {
	content: '标准字体';
}
.ql-snow .ql-picker.ql-font .ql-picker-label[data-value='serif']::before,
.ql-snow .ql-picker.ql-font .ql-picker-item[data-value='serif']::before {
	content: '衬线字体';
}
.ql-snow .ql-picker.ql-font .ql-picker-label[data-value='monospace']::before,
.ql-snow .ql-picker.ql-font .ql-picker-item[data-value='monospace']::before {
	content: '等宽字体';
}

.editor1 {
	background-color: #f5f7fa !important;
	border-color: #e4e7ed !important;
	color: #c0c4cc !important;
	cursor: not-allowed !important;
}
.editor1 > .ql-editor > * {
	cursor: not-allowed !important;
}
.ql-container {
	height: 120px;
}
.ql-container .ql-editor::before {
	color: #c1c4cc; /* 提示语文本颜色 */
	font-size: 14px; /* 字体大小 */
	font-style: normal; /* 字体风格 */
}
.ql-toolbar.ql-snow,
.ql-container.ql-snow {
	border: 1px solid #dcdfe6;
	border-radius: 4px;
}
</style>
